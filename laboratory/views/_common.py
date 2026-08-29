import io
import re
import logging
import hashlib
from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum, Q
from django.utils.dateparse import parse_date
from django.utils import timezone

logger = logging.getLogger(__name__)

# ReportLab Engine Modules
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

# Database App Entities
from ..models import LabTest, Appointment, TestResult, PatientProfile, Payment
from accounts.utils import generate_unique_username, generate_strong_temp_password


# =========================================================================
# APPOINTMENT SLOT CAPACITY CONFIG
# =========================================================================

SLOT_CAPACITY = 5

TIME_SLOTS = [
    "07:00 AM - 08:00 AM",
    "09:00 AM - 10:00 AM",
    "01:00 PM - 02:00 PM",
    "02:00 PM - 03:00 PM",
    "03:00 PM - 04:00 PM",
    "04:00 PM - 05:00 PM",
]

# =========================================================================
# SHARED REPORT-GENERATION HELPERS
# Used by both patient.download_report_view and staff.generate_report_view
# =========================================================================

def _pdf_safe(text):
    """
    ReportLab's base-14 fonts (Helvetica etc.) silently render a blank
    glyph for a handful of common lab-report characters -- most notably
    the micro sign (µ) used in µL / µg/dL -- even though no exception is
    raised. Swap those out for safe ASCII look-alikes so nothing on the
    PDF ever comes out as an invisible gap.
    """
    if text is None:
        return ""
    text = str(text)
    replacements = {
        "\u00b5": "u",   # µ MICRO SIGN
        "\u03bc": "u",   # μ GREEK SMALL LETTER MU
        "\u2013": "-",   # – en dash
        "\u2014": "-",   # — em dash
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u00a0": " ",   # non-breaking space
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text

def _compute_flag(result_value, normal_range):
    """
    Attempts to classify a numeric result against a simple "low-high"
    normal range (e.g. "70-100" or "4.5 - 11.0 x10^3/uL") as LOW / HIGH /
    NORMAL. Composite, multi-parameter ranges (e.g. a CBC panel string
    listing Hb/WBC/Platelets together) can't be safely reduced to one
    number, so those -- and anything non-numeric -- fall back to a
    neutral "REVIEW" flag rather than guessing.
    """
    try:
        value = float(str(result_value).strip())
    except (TypeError, ValueError):
        return "REVIEW", "#64748b"

    range_text = normal_range or ""
    # Only trust a range string that is a single "low-high" pair, not a
    # composite panel listing several parameters (those contain multiple
    # colons/commas and would give a misleading flag).
    if range_text.count(":") > 0 or range_text.count(",") > 0:
        return "REVIEW", "#64748b"

    match = re.search(r"(-?\d+(?:\.\d+)?)\s*[-\u2013]\s*(-?\d+(?:\.\d+)?)", range_text)
    if not match:
        return "REVIEW", "#64748b"

    low, high = float(match.group(1)), float(match.group(2))
    if value < low:
        return "LOW", "#d97706"
    if value > high:
        return "HIGH", "#dc2626"
    return "NORMAL", "#16a34a"

def _parse_range_components(normal_range):
    """
    Splits a composite panel range like
    "Hb: 12-16, WBC: 4,000-11,000, Platelets: 150,000-450,000" into
    [("Hb", "12", "16"), ("WBC", "4,000", "11,000"), ...].
    Regex-based (not a plain comma-split) because the numbers themselves
    can contain thousands-separator commas -- a naive split on "," would
    cut "4,000-11,000" in half. Returns [] if normal_range doesn't look
    like a "Label: low-high" composite string at all.
    """
    if not normal_range:
        return []
    num = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
    pattern = rf"([A-Za-z][A-Za-z0-9 /%]*?)\s*:\s*({num})\s*[-\u2013]\s*({num})"
    return re.findall(pattern, normal_range)

def _parse_result_components(result_value):
    """
    Parses a technician-entered composite result like
    "Hb: 14, WBC: 6500, Platelets: 250000" into
    {"hb": "14", "wbc": "6500", "platelets": "250000"} (lowercased keys
    for tolerant matching against _parse_range_components' labels).
    Returns {} if result_value has no "Label: value" pairs (i.e. it's an
    ordinary single-value result like "98.6").
    """
    if not result_value:
        return {}
    num = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
    pattern = rf"([A-Za-z][A-Za-z0-9 /%]*?)\s*:\s*({num})"
    pairs = re.findall(pattern, result_value)
    return {label.strip().lower(): value.strip() for label, value in pairs}

def _build_panel_rows(result_value, normal_range):
    """
    Tries to line up a composite result (see _parse_result_components)
    against a composite normal range (see _parse_range_components) by
    matching parameter labels, so a CBC-style panel can be rendered as
    one row per parameter (Hb / WBC / Platelets / ...) each with its
    own flag, instead of one opaque combined value.

    Returns a list of (label, value, range_text, flag_text, flag_color)
    tuples on success, or None if the result isn't in the expected
    composite "Label: value, Label: value" format -- callers should
    fall back to the existing single-row rendering in that case.
    """
    range_components = _parse_range_components(normal_range)
    if len(range_components) < 2:
        return None

    result_map = _parse_result_components(result_value)
    if not result_map:
        return None

    rows = []
    for label, low, high in range_components:
        key = label.strip().lower()
        value = result_map.get(key)
        if value is None:
            # Technician's composite entry doesn't cover every parameter
            # the range lists -- safer to fall back than show a blank.
            return None
        range_text = f"{low}-{high}"
        flag_text, flag_color = _compute_flag(
            value.replace(",", ""), f"{low.replace(',', '')}-{high.replace(',', '')}"
        )
        rows.append((label.strip(), value, range_text, flag_text, flag_color))

    return rows

def _resolve_patient_snapshot(appointment):
    """
    Prefer the demographic snapshot captured at booking time
    (Appointment.patient_age / patient_gender / patient_address).
    If that snapshot is empty (e.g. the patient booked before ever
    filling out their profile), fall back to their current
    PatientProfile so the page doesn't just show blanks forever.
    """
    profile = getattr(appointment.patient, 'patient_profile', None)

    age = appointment.patient_age or (profile.age if profile else None)
    gender = appointment.patient_gender or (profile.gender if profile else None)
    address = appointment.patient_address or (profile.address if profile else None)

    gender_display = {'M': 'Male', 'F': 'Female', 'O': 'Other'}.get(gender, '—')

    return {
        'age': age if age else '—',
        'gender_display': gender_display,
        'address': address if address else '—',
    }

def _build_report_pdf_bytes(appointment):
    """
    Renders the certified PDF report for a single appointment and
    returns the raw PDF bytes. Shared by the download view and by
    the "report ready" email so both always produce the exact same
    document.
    """
    snapshot = _resolve_patient_snapshot(appointment)
    test_name = appointment.test.test_name if appointment.test else "N/A"
    normal_range = appointment.test.normal_range if (appointment.test and hasattr(appointment.test, 'normal_range')) else "N/A"
    unit = appointment.test.unit if (appointment.test and hasattr(appointment.test, 'unit')) else ""

    try:
        live_result = appointment.result
        result_value = live_result.result_value or "Pending"
        remarks = (live_result.remarks or "").strip()
        is_verified = bool(live_result.verified)
        verified_by = (
            (live_result.verified_by.full_name or live_result.verified_by.get_full_name() or live_result.verified_by.username)
            if live_result.verified_by else None
        )
        verified_at = live_result.verified_at
    except (TestResult.DoesNotExist, AttributeError):
        result_value = "Pending"
        remarks = ""
        is_verified = False
        verified_by = None
        verified_at = None

    flag_text, flag_color = _compute_flag(result_value, normal_range)

    if hasattr(appointment.appointment_date, 'strftime'):
        # appointment_date is a timezone-aware DateTimeField (stored in
        # UTC). Formatting it directly can print the wrong calendar day
        # for appointments near midnight in Asia/Kathmandu (UTC+5:45) --
        # convert to local time first, same fix as the verification
        # timestamp below.
        formatted_date = timezone.localtime(appointment.appointment_date).strftime('%B %d, %Y')
    else:
        formatted_date = str(appointment.appointment_date)

    # ---------------------------------------------------------------
    # Styles
    # ---------------------------------------------------------------
    styles = getSampleStyleSheet()
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"], fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#64748b"), leading=12,
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5,
        textColor=colors.HexColor("#1e293b"), leading=13,
    )
    cell_style = ParagraphStyle(
        "Cell", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5,
        textColor=colors.HexColor("#1e293b"), leading=12.5,
    )
    cell_bold_style = ParagraphStyle(
        "CellBold", parent=cell_style, fontName="Helvetica-Bold",
    )
    remarks_style = ParagraphStyle(
        "Remarks", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=9.5,
        textColor=colors.HexColor("#334155"), leading=13,
    )

    def field(label, value):
        return [Paragraph(_pdf_safe(label), label_style), Paragraph(_pdf_safe(value), value_style)]

    # ---------------------------------------------------------------
    # Build the flowable story
    # ---------------------------------------------------------------
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=40, rightMargin=40, topMargin=0, bottomMargin=40,
    )
    story = []

    # --- Header banner ---
    header_data = [[
        Paragraph(
            '<font color="white" size="18"><b>LABPORTAL MEDICAL DIAGNOSTICS</b></font>'
            '<br/><font color="#cbd5e1" size="9">Certified Clinical Laboratory Report &mdash; Official Copy</font>',
            ParagraphStyle("HeaderTitle", fontName="Helvetica", leading=16),
        ),
        Paragraph(
            f'<font color="white" size="9">Report ID</font><br/>'
            f'<font color="white" size="13"><b>#LMS-00{appointment.id}</b></font><br/>'
            f'<font color="#4ade80" size="8"><b>&#128274; INTEGRITY-CHECKSUMMED</b></font>',
            ParagraphStyle("HeaderId", alignment=TA_RIGHT, fontName="Helvetica", leading=14),
        ),
    ]]
    header_table = Table(header_data, colWidths=[380, 152])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1a233a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 40),
        ("RIGHTPADDING", (1, 0), (1, 0), 40),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # --- Patient information panel ---
    patient_name = (
        appointment.patient.full_name
        or appointment.patient.get_full_name()
        or appointment.patient.username
    )
    info_rows = [
        [
            field("PATIENT NAME", patient_name),
            field("REPORT DATE", formatted_date),
        ],
        [
            field("EMAIL", appointment.patient.email or "-"),
            field("STATUS", appointment.status),
        ],
        [
            field("AGE / GENDER", f"{snapshot['age']} / {snapshot['gender_display']}"),
            field("ADDRESS", snapshot['address']),
        ],
        [
            field("REFERRAL", "Doctor Referred" if appointment.referral_type == "doctor" else "Self-Referred"),
            field("COLLECTION SLOT", appointment.appointment_time or "-"),
        ],
    ]
    info_table_data = []
    for left, right in info_rows:
        info_table_data.append([left[0], left[1], right[0], right[1]])
    info_table = Table(info_table_data, colWidths=[95, 158, 95, 158])
    info_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, -1), 14),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 14),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 22))

    # --- Results table ---
    story.append(Paragraph(
        "LABORATORY RESULTS",
        ParagraphStyle("SectionTitle", fontName="Helvetica-Bold", fontSize=11,
                        textColor=colors.HexColor("#1a233a"), spaceAfter=8),
    ))

    flag_html = f'<font color="{flag_color}"><b>{_pdf_safe(flag_text)}</b></font>'
    results_header = [
        Paragraph("<b>TEST PARAMETER</b>", cell_bold_style),
        Paragraph("<b>RESULT</b>", cell_bold_style),
        Paragraph("<b>UNIT</b>", cell_bold_style),
        Paragraph("<b>NORMAL RANGE</b>", cell_bold_style),
        Paragraph("<b>FLAG</b>", cell_bold_style),
    ]

    # Panel tests (e.g. CBC) store one composite normal_range covering
    # several parameters ("Hb: 12-16, WBC: 4,000-11,000, ..."). If the
    # technician entered a matching composite result ("Hb: 14, WBC:
    # 6500, ..."), show one row per parameter with its own flag instead
    # of one opaque combined row. Falls back to the original single-row
    # layout for ordinary (non-panel) tests, or if the composite result
    # doesn't parse cleanly.
    panel_rows = _build_panel_rows(result_value, normal_range)

    results_body_rows = []
    if panel_rows:
        for label, value, range_text, row_flag_text, row_flag_color in panel_rows:
            row_flag_html = f'<font color="{row_flag_color}"><b>{_pdf_safe(row_flag_text)}</b></font>'
            results_body_rows.append([
                Paragraph(_pdf_safe(f"{test_name} \u2013 {label}"), cell_style),
                Paragraph(f"<b>{_pdf_safe(value)}</b>", cell_bold_style),
                Paragraph(_pdf_safe(unit), cell_style),
                Paragraph(_pdf_safe(range_text), cell_style),
                Paragraph(row_flag_html, cell_style),
            ])
    else:
        results_body_rows.append([
            Paragraph(_pdf_safe(test_name), cell_style),
            Paragraph(f"<b>{_pdf_safe(result_value)}</b>", cell_bold_style),
            Paragraph(_pdf_safe(unit), cell_style),
            Paragraph(_pdf_safe(normal_range), cell_style),
            Paragraph(flag_html, cell_style),
        ])

    results_table = Table(
        [results_header] + results_body_rows,
        colWidths=[140, 65, 75, 155, 65],
    )
    results_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white]),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Flags marked REVIEW indicate a composite/panel result or a non-numeric value that a clinician "
        "should interpret directly rather than an automated low/high comparison.",
        ParagraphStyle("FootNote", fontName="Helvetica-Oblique", fontSize=7.5,
                        textColor=colors.HexColor("#94a3b8")),
    ))
    story.append(Spacer(1, 22))

    # --- Clinical remarks ---
    story.append(Paragraph(
        "CLINICAL REMARKS",
        ParagraphStyle("SectionTitle2", fontName="Helvetica-Bold", fontSize=11,
                        textColor=colors.HexColor("#1a233a"), spaceAfter=8),
    ))
    remarks_box_data = [[Paragraph(
        _pdf_safe(remarks) if remarks else "No additional remarks were recorded for this test.",
        remarks_style,
    )]]
    remarks_table = Table(remarks_box_data, colWidths=[532])
    remarks_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(remarks_table)
    story.append(Spacer(1, 22))

    # --- Verification / sign-off ---
    if is_verified and verified_by:
        # verified_at is stored as a UTC-aware datetime (timezone.now()).
        # Formatting it directly with .strftime() prints the raw UTC
        # clock time, not the project's local time (Asia/Kathmandu,
        # UTC+5:45) -- that's why the report showed a time nearly 6
        # hours behind the wall clock. Convert to local time first.
        local_verified_at = timezone.localtime(verified_at) if verified_at else None
        verified_line = (
            f'<font color="#16a34a"><b>&#10003; VERIFIED</b></font> by {_pdf_safe(verified_by)}'
            f' on {local_verified_at.strftime("%B %d, %Y %I:%M %p") if local_verified_at else "-"}'
        )
    else:
        verified_line = '<font color="#d97706"><b>PENDING VERIFICATION</b></font> &mdash; awaiting authorized sign-off'
    story.append(Paragraph(verified_line, ParagraphStyle(
        "Verify", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#334155"),
    )))
    story.append(Spacer(1, 10))

    # --- Blockchain verification badge ---
    # Demo/UI feature only: shows a deterministic mock hash "anchoring"
    # this report so the PDF looks tamper-evident. Not a real on-chain
    # record -- there's no external ledger call here, just a stable
    # hash derived from the report's own data so the same report always
    # renders the same hash.
    record_fingerprint = "|".join([
        str(appointment.id), test_name, str(result_value), str(is_verified),
    ])
    blockchain_hash = hashlib.sha256(record_fingerprint.encode("utf-8")).hexdigest()

    # QR payload: a compact plain-text summary a phone's camera can read
    # directly (no external site needed) -- report id + full hash, so
    # anyone scanning it can visually diff it against the printed hash.
    qr_payload = (
        f"LabPortal Report #LMS-00{appointment.id}\n"
        f"SHA-256: {blockchain_hash}"
    )
    qr_code = qr.QrCodeWidget(qr_payload)
    qr_code.barLevel = 'M'
    qr_bounds = qr_code.getBounds()
    qr_size = 70
    qr_scale = qr_size / (qr_bounds[2] - qr_bounds[0])
    qr_drawing = Drawing(qr_size, qr_size, transform=[qr_scale, 0, 0, qr_scale, 0, 0])
    qr_drawing.add(qr_code)

    blockchain_data = [[
        Paragraph(
            '<font color="#16a34a" size="9"><b>&#128274; INTEGRITY-CHECKSUMMED</b></font><br/>'
            '<font color="#64748b" size="7.5">This report\'s data is sealed with a cryptographic '
            'hash below. Any change to the results would produce a different hash. '
            'Scan the code to compare it.</font>',
            ParagraphStyle("ChainLabel", fontName="Helvetica", leading=11),
        ),
        qr_drawing,
        Paragraph(
            f'<font color="#64748b" size="7">RECORD HASH (SHA-256)</font><br/>'
            f'<font color="#1a233a" size="8"><b>{blockchain_hash[:32]}</b></font><br/>'
            f'<font color="#1a233a" size="8"><b>{blockchain_hash[32:]}</b></font>',
            ParagraphStyle("ChainHash", alignment=TA_RIGHT, fontName="Courier", leading=11),
        ),
    ]]
    blockchain_table = Table(blockchain_data, colWidths=[218, 82, 232])
    blockchain_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bbf7d0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (0, -1), 14),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 14),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(blockchain_table)
    story.append(Spacer(1, 14))

    story.append(HRFlowable(width="100%", color=colors.HexColor("#cbd5e1"), thickness=0.75))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "* This is a digitally generated laboratory report issued by LabPortal Medical Diagnostics. "
        "Authorized signatures are held on file within our secure records infrastructure.",
        ParagraphStyle("Disclaimer", fontName="Helvetica-Oblique", fontSize=8,
                        textColor=colors.HexColor("#64748b")),
    ))

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()

def _send_report_ready_email(appointment):
    """
    Fired the moment a technician verifies/signs a report (the same
    action that makes it visible on the patient's dashboard). Emails
    the patient that their report is ready, with the certified PDF
    attached. Failures are logged but never interrupt the technician's
    workflow -- a failed email should not block a signed report.
    """
    patient = appointment.patient
    if not patient.email:
        return False

    try:
        pdf_bytes = _build_report_pdf_bytes(appointment)

        patient_name = patient.full_name or patient.get_full_name() or patient.username
        test_name = appointment.test.test_name if appointment.test else "your requested test"
        report_url = settings.SITE_URL.rstrip('/') + reverse('patient_reports')

        subject = f"Your Lab Report is Ready — Appointment #LMS-00{appointment.id}"

        text_body = (
            f"Hi {patient_name},\n\n"
            f"Your laboratory report for \"{test_name}\" (Appointment #LMS-00{appointment.id}) "
            f"has been reviewed, signed, and is now ready.\n\n"
            f"The certified PDF is attached to this email, and you can also view or "
            f"re-download it anytime from your dashboard:\n{report_url}\n\n"
            f"— LabPortal Medical Diagnostics"
        )

        html_body = f"""
        <div style="font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;max-width:520px;margin:0 auto;">
          <div style="background:#0f172a;padding:20px 24px;border-radius:8px 8px 0 0;">
            <span style="color:#fff;font-size:16px;font-weight:700;">LabPortal Medical Diagnostics</span>
          </div>
          <div style="border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;padding:24px;">
            <p style="font-size:15px;color:#1e293b;">Hi {patient_name},</p>
            <p style="font-size:14px;color:#334155;line-height:1.6;">
              Your laboratory report for <b>{test_name}</b>
              (Appointment <b>#LMS-00{appointment.id}</b>) has been reviewed, signed,
              and is now ready.
            </p>
            <p style="font-size:14px;color:#334155;line-height:1.6;">
              The certified PDF is attached to this email. You can also view or
              re-download it anytime from your dashboard.
            </p>
            <p style="margin:24px 0;">
              <a href="{report_url}"
                 style="background:#2563eb;color:#fff;text-decoration:none;padding:10px 20px;
                        border-radius:6px;font-size:14px;font-weight:600;display:inline-block;">
                View My Reports
              </a>
            </p>
            <p style="font-size:12px;color:#94a3b8;margin-top:24px;">
              This is an automated notification from LabPortal Medical Diagnostics.
            </p>
          </div>
        </div>
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.attach(f"LabReport_00{appointment.id}.pdf", pdf_bytes, "application/pdf")
        email.send(fail_silently=False)
        return True

    except Exception:
        logger.exception(
            "Failed to send report-ready email for appointment #%s", appointment.id
        )
        return False

