"""
Tests for the AI report chat assistant: laboratory/ai_report_chat.py plus
the report_chat_view endpoint it backs.

No real network calls are made -- requests.post is mocked throughout, so
these run without an ANTHROPIC_API_KEY and without hitting the internet.

Run with:
    python manage.py test laboratory.tests_ai_report_chat
"""
import json
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from laboratory.models import TestCategory, LabTest, Appointment, TestResult
from laboratory.ai_report_chat import build_report_context, ask_report_question

User = get_user_model()


def make_completed_appointment(patient, result_value="180", normal_range="70-100", verified=True):
    category, _ = TestCategory.objects.get_or_create(name="Chemistry")
    test = LabTest.objects.create(
        category=category, test_name="Fasting Blood Sugar",
        price="500.00", normal_range=normal_range, unit="mg/dL",
    )
    appointment = Appointment.objects.create(
        patient=patient, test=test, appointment_date=timezone.now(),
        status="Completed",
    )
    TestResult.objects.create(
        appointment=appointment, result_value=result_value,
        remarks="Patient was fasting for 10 hours.", verified=verified,
    )
    return appointment


def mock_anthropic_response(text="Here is a plain-language explanation."):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"content": [{"type": "text", "text": text}]}
    return resp


class BuildReportContextTests(TestCase):

    def setUp(self):
        self.patient = User.objects.create_user(username="pat1", password="x", email="pat1@example.com")

    def test_context_includes_expected_fields_and_flags_high(self):
        appointment = make_completed_appointment(self.patient, result_value="180", normal_range="70-100")
        ctx = build_report_context(appointment)
        self.assertEqual(ctx['test_name'], "Fasting Blood Sugar")
        self.assertEqual(ctx['result_value'], "180")
        self.assertEqual(ctx['unit'], "mg/dL")
        self.assertEqual(ctx['normal_range'], "70-100")
        self.assertEqual(ctx['flag'], "HIGH")
        self.assertIn("fasting", ctx['remarks'].lower())
        self.assertEqual(ctx['verified'], "Yes")

    def test_context_flags_normal_result(self):
        appointment = make_completed_appointment(self.patient, result_value="90", normal_range="70-100")
        ctx = build_report_context(appointment)
        self.assertEqual(ctx['flag'], "NORMAL")

    def test_context_never_leaks_patient_identity(self):
        """The AI is only shown test/result data -- no name, email, or
        address should ever end up in the system-prompt context dict."""
        appointment = make_completed_appointment(self.patient)
        ctx = build_report_context(appointment)
        serialized = json.dumps(ctx)
        self.assertNotIn(self.patient.username, serialized)
        self.assertNotIn(self.patient.email, serialized)


@override_settings(ANTHROPIC_API_KEY="test-key-123", ANTHROPIC_MODEL="claude-sonnet-5")
class AskReportQuestionTests(TestCase):

    def setUp(self):
        self.patient = User.objects.create_user(username="pat2", password="x", email="pat2@example.com")
        self.appointment = make_completed_appointment(self.patient, result_value="180", normal_range="70-100")

    @patch("laboratory.ai_report_chat.requests.post")
    def test_successful_call_returns_answer(self, mock_post):
        mock_post.return_value = mock_anthropic_response("Your result is a bit above the usual range.")
        answer, error = ask_report_question(self.appointment, "What does HIGH mean?")
        self.assertIsNone(error)
        self.assertIn("above the usual range", answer)
        mock_post.assert_called_once()

    @patch("laboratory.ai_report_chat.requests.post")
    def test_system_prompt_is_grounded_in_this_report(self, mock_post):
        """The system prompt sent to the API must actually contain this
        appointment's real result value and flag -- not be generic."""
        mock_post.return_value = mock_anthropic_response()
        ask_report_question(self.appointment, "Explain this")
        _, kwargs = mock_post.call_args
        system_prompt = kwargs['json']['system']
        self.assertIn("Fasting Blood Sugar", system_prompt)
        self.assertIn("180", system_prompt)
        self.assertIn("HIGH", system_prompt)

    @patch("laboratory.ai_report_chat.requests.post")
    def test_history_is_forwarded_and_trimmed(self, mock_post):
        mock_post.return_value = mock_anthropic_response()
        long_history = [{"role": "user", "content": f"q{i}"} for i in range(30)]
        ask_report_question(self.appointment, "one more question", history=long_history)
        _, kwargs = mock_post.call_args
        sent_messages = kwargs['json']['messages']
        # trimmed history + the new question appended
        self.assertLessEqual(len(sent_messages), 13)
        self.assertEqual(sent_messages[-1], {"role": "user", "content": "one more question"})

    def test_empty_question_rejected_without_network_call(self):
        with patch("laboratory.ai_report_chat.requests.post") as mock_post:
            answer, error = ask_report_question(self.appointment, "   ")
            self.assertIsNone(answer)
            self.assertIsNotNone(error)
            mock_post.assert_not_called()

    def test_overlong_question_rejected_without_network_call(self):
        with patch("laboratory.ai_report_chat.requests.post") as mock_post:
            answer, error = ask_report_question(self.appointment, "x" * 5000)
            self.assertIsNone(answer)
            self.assertIsNotNone(error)
            mock_post.assert_not_called()

    @override_settings(ANTHROPIC_API_KEY="")
    def test_missing_api_key_fails_closed_without_network_call(self):
        with patch("laboratory.ai_report_chat.requests.post") as mock_post:
            answer, error = ask_report_question(self.appointment, "Hello?")
            self.assertIsNone(answer)
            self.assertIn("configured", error)
            mock_post.assert_not_called()

    @patch("laboratory.ai_report_chat.requests.post")
    def test_api_error_status_returns_friendly_message_not_raw_body(self, mock_post):
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "internal server meltdown with secret stack trace"
        mock_post.return_value = resp
        answer, error = ask_report_question(self.appointment, "Hello?")
        self.assertIsNone(answer)
        self.assertNotIn("stack trace", error)

    @patch("laboratory.ai_report_chat.requests.post")
    def test_network_exception_does_not_raise(self, mock_post):
        import requests
        mock_post.side_effect = requests.ConnectionError("boom")
        answer, error = ask_report_question(self.appointment, "Hello?")
        self.assertIsNone(answer)
        self.assertIsNotNone(error)


@override_settings(ANTHROPIC_API_KEY="test-key-123")
class ReportChatViewTests(TestCase):

    def setUp(self):
        self.patient = User.objects.create_user(username="pat3", password="pw12345", email="pat3@example.com")
        self.other_patient = User.objects.create_user(username="pat4", password="pw12345", email="pat4@example.com")
        self.appointment = make_completed_appointment(self.patient)
        self.client.login(username="pat3", password="pw12345")

    def _url(self):
        return reverse('report_chat', kwargs={'appointment_id': self.appointment.id})

    @patch("laboratory.views.patient.ask_report_question")
    def test_owner_can_chat_about_their_own_completed_report(self, mock_ask):
        mock_ask.return_value = ("It means your level is above the typical range.", None)
        response = self.client.post(
            self._url(), data=json.dumps({"question": "What does HIGH mean?", "history": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("above the typical range", response.json()['answer'])

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(
            self._url(), data=json.dumps({"question": "Hi"}), content_type="application/json",
        )
        self.assertIn(response.status_code, (302, 401, 403))

    def test_other_patient_cannot_access_someone_elses_report_chat(self):
        self.client.logout()
        self.client.login(username="pat4", password="pw12345")
        response = self.client.post(
            self._url(), data=json.dumps({"question": "Hi"}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_rejects_chat_on_a_not_yet_completed_report(self):
        pending_appt = make_completed_appointment(self.patient)
        pending_appt.status = 'Pending'
        pending_appt.save()
        url = reverse('report_chat', kwargs={'appointment_id': pending_appt.id})
        response = self.client.post(
            url, data=json.dumps({"question": "Hi"}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_get_request_not_allowed(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 405)

    def test_malformed_json_body_handled_gracefully(self):
        response = self.client.post(self._url(), data="not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("laboratory.views.patient.ask_report_question")
    def test_malformed_history_items_from_client_are_dropped(self, mock_ask):
        """A client could send garbage in 'history' -- the view must
        sanitize it down to well-formed turns before ever calling the
        AI helper, rather than forwarding it as-is."""
        mock_ask.return_value = ("ok", None)
        bad_history = [
            {"role": "user", "content": "fine"},
            {"role": "system", "content": "trying to inject a role"},
            "not even a dict",
            {"role": "user"},  # no content
        ]
        self.client.post(
            self._url(),
            data=json.dumps({"question": "Hi", "history": bad_history}),
            content_type="application/json",
        )
        called_history = mock_ask.call_args.kwargs['history']
        self.assertEqual(called_history, [{"role": "user", "content": "fine"}])
