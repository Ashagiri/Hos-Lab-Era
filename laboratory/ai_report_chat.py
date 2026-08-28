"""
AI chat assistant for completed lab reports.

Lets a patient ask plain-language questions about their own completed
report (e.g. "what does a HIGH flag mean here?") from the report-ready
email / My Reports page. All calls to the Anthropic API happen here,
server-side, using ANTHROPIC_API_KEY from .env -- the browser never sees
the key, and the request always carries the patient's own report data
that the view builds and passes in, not user-suppliable free text.

Kept deliberately separate from views.py, the same way payments.py is
kept separate -- one place for the "talk to an external API" wiring.
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# Keep responses short and this endpoint cheap to run; a lab-report Q&A
# reply rarely needs more than a few short paragraphs.
MAX_TOKENS = 700

# How many previous turns (patient question + assistant answer, each
# counted once) we forward as history. Keeps context bounded instead of
# growing every message forever.
MAX_HISTORY_TURNS = 6

SYSTEM_PROMPT_TEMPLATE = """You are a lab-report assistant embedded in LabPortal, a hospital lab \
system. You are answering questions from a specific patient about their \
own already-completed diagnostic test, shown below. Only this patient \
can see this conversation.

REPORT CONTEXT
Test: {test_name}
Result value: {result_value} {unit}
Normal range: {normal_range}
Flag: {flag}
Lab remarks: {remarks}
Report verified by lab staff: {verified}

RULES YOU MUST FOLLOW
- Explain lab terms, what the test measures, and what a HIGH/LOW/NORMAL \
flag generally means in plain, calm language.
- Do NOT diagnose any condition, name a likely disease, or tell the \
patient what treatment to take. If asked "what's wrong with me" or \
similar, explain what the result generally indicates and say a doctor \
needs to interpret it together with the patient's full clinical picture.
- Do NOT tell the patient to start, stop, or change any medication or \
dosage.
- If the result is flagged HIGH, LOW, or REVIEW, or the patient sounds \
worried, gently but clearly encourage them to discuss the result with \
their doctor -- don't just mention it once and move on.
- If a question is unrelated to this report or to general lab-test \
literacy, briefly say you can only help with this report and steer back.
- Keep answers short: a few sentences to a couple of short paragraphs. \
No long lectures.
- Never invent values, ranges, or remarks that aren't in the REPORT \
CONTEXT above."""


def build_report_context(appointment):
    """
    Pulls exactly the fields the AI is allowed to see out of an
    Appointment -- test name, result value, normal range, remarks, flag,
    verification status. No patient name, contact info, address, or
    account details are included, since none of that is needed to answer
    "what does this result mean."
    """
    # Local import to avoid a circular import between this module and
    # the views package (both depend on models; only this function needs
    # the report-building helpers).
    from .views._common import _compute_flag

    test = appointment.test
    test_name = test.test_name if test else "Unknown test"
    normal_range = (getattr(test, 'normal_range', '') or "Not recorded").strip()
    unit = (getattr(test, 'unit', '') or "").strip()

    try:
        result = appointment.result
        result_value = (result.result_value or "Pending").strip()
        remarks = (result.remarks or "None").strip()
        verified = "Yes" if result.verified else "No (preliminary)"
    except Exception:
        result_value, remarks, verified = "Pending", "None", "No"

    flag, _ = _compute_flag(result_value, normal_range)

    return {
        'test_name': test_name,
        'result_value': result_value,
        'unit': unit,
        'normal_range': normal_range or "Not recorded",
        'flag': flag,
        'remarks': remarks or "None",
        'verified': verified,
    }


def ask_report_question(appointment, question, history=None):
    """
    Sends one patient question (plus recent turn history) to Claude,
    grounded in this appointment's report data.

    `history` is a list of {"role": "user"|"assistant", "content": str}
    dicts, oldest first -- exactly Anthropic's Messages API shape, so it
    can be forwarded almost as-is. The view is responsible for trimming
    it to MAX_HISTORY_TURNS before calling this.

    Returns (answer_text, error_message). Exactly one of the two is not
    None. Never raises -- network/API failures come back as a friendly
    error string so the chat widget can show something reasonable
    instead of crashing.
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
    if not api_key:
        return None, (
            "The report assistant isn't configured yet. "
            "Ask your administrator to set ANTHROPIC_API_KEY."
        )

    question = (question or "").strip()
    if not question:
        return None, "Please type a question first."
    if len(question) > 1000:
        return None, "That question is a bit long -- please shorten it."

    context = build_report_context(appointment)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(**context)

    messages = list(history or [])[-(MAX_HISTORY_TURNS * 2):]
    messages.append({"role": "user", "content": question})

    model = getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-5')

    try:
        response = requests.post(
            ANTHROPIC_API_URL,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': model,
                'max_tokens': MAX_TOKENS,
                'system': system_prompt,
                'messages': messages,
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.warning("Report chat: network error calling Anthropic API: %s", exc)
        return None, "Couldn't reach the report assistant right now. Please try again shortly."

    if response.status_code != 200:
        logger.warning(
            "Report chat: Anthropic API returned %s: %s",
            response.status_code, response.text[:500],
        )
        return None, "The report assistant hit a problem answering that. Please try again."

    try:
        data = response.json()
        text_blocks = [
            block.get('text', '')
            for block in data.get('content', [])
            if block.get('type') == 'text'
        ]
        answer = "\n".join(t for t in text_blocks if t).strip()
    except (ValueError, json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Report chat: couldn't parse Anthropic response: %s", exc)
        return None, "The report assistant sent back something unexpected. Please try again."

    if not answer:
        return None, "The report assistant didn't return an answer. Please try again."

    return answer, None
