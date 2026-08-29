import io
import json
import re
import logging
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

# Database App Entities
from ..models import LabTest, Appointment, TestResult, PatientProfile, Payment
from ..ai_report_chat import ask_report_question
from accounts.utils import generate_unique_username, generate_strong_temp_password
from accounts.decorators import is_lab_staff


from ._common import _build_report_pdf_bytes, SLOT_CAPACITY, TIME_SLOTS

def _slot_patient_count(appointment_date, appointment_time, exclude_patient_id=None):
    """
    Counts how many DISTINCT patients already hold an active (Pending/Completed)
    appointment for the given date + time slot.
    """
    qs = Appointment.objects.filter(
        appointment_date__date=appointment_date,
        appointment_time=appointment_time,
        status__in=['Pending', 'Completed'],
    )
    if exclude_patient_id is not None:
        qs = qs.exclude(patient_id=exclude_patient_id)
    return qs.values('patient_id').distinct().count()

def _next_available_slot(appointment_date, requested_slot, exclude_patient_id):
    """
    Looks at the slots that come AFTER requested_slot in TIME_SLOTS order
    and returns the first one that still has room.
    """
    try:
        start_index = TIME_SLOTS.index(requested_slot)
    except ValueError:
        start_index = -1

    for slot in TIME_SLOTS[start_index + 1:]:
        if _slot_patient_count(appointment_date, slot, exclude_patient_id) < SLOT_CAPACITY:
            return slot
    return None


# =========================================================================
# STATIC DISPLAY METADATA
# =========================================================================

TEST_DISPLAY_INFO = {
    "Complete Blood Count (CBC)": {"icon": "🩸", "desc": "Measures different components of your blood"},
    "Dengue NS1 Antigen": {"icon": "🦟", "desc": "Detects active dengue virus or immune response antibodies"},
    "Tuberculosis (TB)": {"icon": "🫁", "desc": "Detects exposure, latent infection, or active immune response to TB bacteria"},
    "X-Ray": {"icon": "☠️", "desc": "Advanced digital imaging for internal bone structures and chest analysis"},
    "Video X-Ray": {"icon": "☠️", "desc": "Advanced digital imaging for internal bone structures and chest analysis"},
    "Vitamin B12 Test": {"icon": "💊", "desc": "Measures Vitamin B12 levels to check for deficiencies or anemia flags"},
    "Urinalysis & Stool Examination": {"icon": "🧪", "desc": "Complete chemical, physical, and microscopic evaluation for metabolic or infection markers"},
    "Cancer Test": {"icon": "🧪", "desc": "Complete chemical, physical, and microscopic evaluation for metabolic or infection markers"},
}


# =========================================================================
# SYSTEM MARKETING ENTRY VIEW
# =========================================================================

def home_view(request):
    """
    Renders the primary landing marketing homepage.
    """
    return render(request, 'laboratory/home.html')


# =========================================================================
# CORE WORKSPACE DASHBOARDS
# =========================================================================

@login_required
def dashboard_view(request):
    """
    Patient Workspace Dashboard.
    """
    user = request.user
    appointments = Appointment.objects.filter(patient=user).order_by('-appointment_date')

    is_returning_user = False
    if user.last_login and user.date_joined:
        login_gap = (user.last_login - user.date_joined).total_seconds()
        if login_gap > 30:
            is_returning_user = True

    context = {
        'appointments': appointments,
        'is_returning_user': is_returning_user,
    }
    return render(request, 'laboratory/dashboard.html', context)

@login_required
def booking_view(request):
    """
    Handles diagnostic test booking creation and pre-fills user profile metadata.
    """
    user = request.user
    patient_prof, _ = PatientProfile.objects.get_or_create(
        user=user,
        defaults={'age': 0, 'gender': 'M', 'address': ''}
    )

    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        selected_test_ids = request.POST.getlist('tests')

        # Extract submitted profile data and persist to PatientProfile
        address_input = request.POST.get('address')
        age_input = request.POST.get('age')
        gender_input = request.POST.get('gender')

        # Extract referral / preferred doctor data (captured but never
        # persisted before -- now saved onto the Appointment itself)
        referral_type = request.POST.get('referral_type', 'self')
        doctor_name = request.POST.get('doctor_name', '').strip()
        doctor_id = request.POST.get('doctor_id', '').strip()

        if address_input is not None:
            patient_prof.address = address_input.strip()

        if age_input and str(age_input).isdigit():
            patient_prof.age = int(age_input)

        if gender_input:
            gender_map = {'Male': 'M', 'Female': 'F', 'Other': 'O', 'M': 'M', 'F': 'F', 'O': 'O'}
            patient_prof.gender = gender_map.get(gender_input, 'M')

        patient_prof.save()

        if not selected_test_ids or not appointment_date or not appointment_time:
            messages.error(request, "Please select at least one test, date, and time slot.")
            return redirect('booking')

        parsed_date = parse_date(appointment_date)
        if parsed_date is None:
            messages.error(request, "Invalid appointment date. Please try again.")
            return redirect('booking')

        existing_patient_count = _slot_patient_count(
            parsed_date, appointment_time, exclude_patient_id=user.id
        )
        if existing_patient_count >= SLOT_CAPACITY:
            suggested_slot = _next_available_slot(parsed_date, appointment_time, user.id)
            if suggested_slot:
                messages.error(
                    request,
                    f"The {appointment_time} slot on {parsed_date.strftime('%B %d, %Y')} is full "
                    f"({SLOT_CAPACITY}/{SLOT_CAPACITY} booked). "
                    f"Please select {suggested_slot} instead."
                )
            else:
                messages.error(
                    request,
                    f"The {appointment_time} slot on {parsed_date.strftime('%B %d, %Y')} is full, "
                    "and no later slots are available that day. Please choose a different date."
                )
            return redirect('booking')

        try:
            created_appointments = []
            total_amount = 0
            for test_id in selected_test_ids:
                test_instance = LabTest.objects.get(id=test_id)

                appointment = Appointment.objects.create(
                    patient=user,
                    test=test_instance,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    status='Pending',
                    referral_type=referral_type,
                    doctor_name=doctor_name if referral_type == 'doctor' else '',
                    doctor_id=doctor_id if referral_type == 'doctor' else '',
                    patient_address=patient_prof.address,
                    patient_age=patient_prof.age,
                    patient_gender=patient_prof.gender,
                )
                created_appointments.append(appointment)
                total_amount += test_instance.price

            # Bundle every test booked in this single trip through the
            # form into one Payment so the patient pays once, via
            # whichever gateway (eSewa / Khalti / Fonepay / NIC Asia /
            # cash at the lab) they pick on the next screen.
            payment = Payment.objects.create(
                patient=user,
                amount=total_amount,
            )
            payment.appointments.set(created_appointments)

            messages.success(request, "Your laboratory test session has been booked! Please complete payment to confirm it.")
            return redirect('payment_select', transaction_uuid=payment.transaction_uuid)

        except LabTest.DoesNotExist:
            messages.error(request, "One or more selected tests could not be found. Please try again.")
            return redirect('booking')
        except Exception as e:
            messages.error(request, f"Error while writing booking to database: {str(e)}")
            return redirect('booking')

    # GET Request: Fetch laboratory test lists
    all_tests = LabTest.objects.all().select_related('category')

    for test in all_tests:
        info = TEST_DISPLAY_INFO.get(test.test_name, {"icon": "🧪", "desc": ""})
        test.icon = info["icon"]
        test.display_desc = info["desc"]

    # Gender formatting for template view
    gender_display_map = {'M': 'Male', 'F': 'Female', 'O': 'Other'}
    formatted_gender = gender_display_map.get(patient_prof.gender, 'Male')

    # Retrieve address from PatientProfile; fall back to last Appointment if empty
    clean_address = patient_prof.address or ''
    if not clean_address.strip() or clean_address.strip().lower() == 'none':
        last_appt = Appointment.objects.filter(patient=user).order_by('-created_at').first()
        if last_appt and hasattr(last_appt, 'address') and last_appt.address:
            clean_address = last_appt.address.strip()

    profile_data = {
        'full_name': user.full_name or user.get_full_name() or user.username,
        'email': user.email or '',
        'address': clean_address,
        'age': patient_prof.age if patient_prof.age is not None else 0,
        'gender': formatted_gender,
    }

    return render(request, 'laboratory/booking.html', {
        'tests': all_tests,
        'user_info': profile_data,
    })

@login_required
def patient_reports_view(request):
    """
    Dedicated, standalone "My Reports" page for patients -- lists every
    appointment the logged-in patient has made, with the ability to
    download a certified PDF for any completed one.
    """
    user = request.user
    appointments = Appointment.objects.filter(patient=user).select_related('test').order_by('-appointment_date')

    status_filter = request.GET.get('status', '').strip()
    if status_filter in ('Pending', 'Completed', 'Cancelled'):
        appointments = appointments.filter(status=status_filter)

    total_count = Appointment.objects.filter(patient=user).count()
    completed_count = Appointment.objects.filter(patient=user, status='Completed').count()
    pending_count = Appointment.objects.filter(patient=user, status='Pending').count()

    return render(request, 'laboratory/patient_reports.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
    })

@login_required
def booking_status_view(request):
    """
    Dedicated "Bookings Status" page for patients -- a live tracker showing
    every appointment the logged-in patient holds, its stage in the
    workflow (Booked -> Sample Collection -> Processing -> Report Ready),
    and lets a patient cancel a still-pending booking.
    """
    user = request.user
    appointments = Appointment.objects.filter(patient=user).select_related('test').order_by('-appointment_date')

    status_filter = request.GET.get('status', '').strip()
    if status_filter in ('Pending', 'Completed', 'Cancelled'):
        appointments = appointments.filter(status=status_filter)

    base_qs = Appointment.objects.filter(patient=user)
    total_count = base_qs.count()
    completed_count = base_qs.filter(status='Completed').count()
    pending_count = base_qs.filter(status='Pending').count()
    cancelled_count = base_qs.filter(status='Cancelled').count()

    return render(request, 'laboratory/booking_status.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
    })

@login_required
def cancel_booking_view(request, appointment_id):
    """
    Lets a patient cancel their own still-pending appointment directly
    from the Bookings Status tracker.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    if request.method == 'POST':
        if appointment.status == 'Pending':
            appointment.status = 'Cancelled'
            appointment.save()
            messages.success(request, f"Booking #LMS-00{appointment.id} has been cancelled.")
        else:
            messages.error(request, "Only pending bookings can be cancelled.")

    return redirect('booking_status')

@login_required
def check_slot_availability(request):
    """
    Returns JSON with time slots availability.
    """
    date_str = request.GET.get('date')
    parsed_date = parse_date(date_str) if date_str else None

    if parsed_date is None:
        return JsonResponse({'error': 'A valid date query parameter is required.'}, status=400)

    slots = {}
    for slot in TIME_SLOTS:
        booked = _slot_patient_count(parsed_date, slot, exclude_patient_id=request.user.id)
        slots[slot] = {
            'booked': booked,
            'capacity': SLOT_CAPACITY,
            'full': booked >= SLOT_CAPACITY,
        }

    return JsonResponse({'date': date_str, 'slots': slots})


# =========================================================================
# DIAGNOSTIC DATA ENTRY & PROCESSING (STAFF ONLY)
# =========================================================================

@login_required
def settings_view(request):
    """
    Manages personal account field updates and security password resets.
    """
    user = request.user
    patient_prof, _ = PatientProfile.objects.get_or_create(
        user=user,
        defaults={'age': 0, 'gender': 'M', 'address': ''}
    )

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            if hasattr(user, 'full_name'):
                user.full_name = full_name

        user.email = request.POST.get('email', user.email)
        user.save()

        address_val = request.POST.get('address')
        if address_val is not None:
            patient_prof.address = address_val.strip()

        age_val = request.POST.get('age')
        if age_val and str(age_val).isdigit():
            patient_prof.age = int(age_val)

        gender_val = request.POST.get('gender')
        if gender_val in ['M', 'F', 'O']:
            patient_prof.gender = gender_val

        patient_prof.save()

        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password or confirm_password:
            if not user.check_password(current_password):
                messages.error(request, "Your current password was entered incorrectly.")
            elif new_password != confirm_password:
                messages.error(request, "The new passwords do not match.")
            else:
                try:
                    validate_password(new_password, user=user)
                except ValidationError as e:
                    for err in e.messages:
                        messages.error(request, err)
                    return redirect('settings')
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password parameters modified successfully.")
        else:
            messages.success(request, "Account details saved successfully.")

        return redirect('settings')

    return render(request, 'laboratory/settings.html', {'patient_profile': patient_prof})


# =========================================================================
# PATIENT SCHEDULING OPERATIONS
# =========================================================================

@login_required
def download_report_view(request, appointment_id):
    if is_lab_staff(request.user):
        appointment = get_object_or_404(Appointment, id=appointment_id)
    else:
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    pdf_bytes = _build_report_pdf_bytes(appointment)
    return FileResponse(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        filename=f"LabReport_00{appointment.id}.pdf",
    )


# =========================================================================
# AI REPORT CHAT ASSISTANT
# Patients ask plain-language questions about a completed report, either
# from the My Reports page or a link in the "report ready" email. Stateless
# server-side: the browser holds the running conversation and resends it
# each turn, so nothing about the chat is persisted in the database.
# =========================================================================

@login_required
def report_chat_view(request, appointment_id):
    """
    POST endpoint (JSON in, JSON out) backing the "Ask AI about this
    report" widget. Only the owning patient can chat about their own
    report, and only once it's actually Completed -- there's nothing
    useful (and potentially confusing) to discuss before then.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)

    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    if appointment.status != 'Completed':
        return JsonResponse(
            {'error': 'This report isn\'t ready yet, so there\'s nothing to discuss.'},
            status=400,
        )

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    question = (body.get('question') or '').strip()
    raw_history = body.get('history') or []

    # Only forward the well-formed shape Anthropic's API expects --
    # never trust the client's history blob verbatim.
    history = [
        {'role': turn.get('role'), 'content': str(turn.get('content', ''))[:2000]}
        for turn in raw_history
        if isinstance(turn, dict) and turn.get('role') in ('user', 'assistant') and turn.get('content')
    ][-12:]

    answer, error = ask_report_question(appointment, question, history=history)
    if error:
        return JsonResponse({'error': error}, status=502 if answer is None else 200)

    return JsonResponse({'answer': answer})
