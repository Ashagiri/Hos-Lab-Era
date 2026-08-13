import io
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
from .models import LabTest, Appointment, TestResult, PatientProfile, Payment
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
def technician_dashboard_view(request):
    """
    Technician Overview Dashboard.
    """
    is_tech = (
        (hasattr(request.user, 'role') and request.user.role == 'technician')
        or request.user.username == 'tech'
        or request.user.is_superuser
    )
    if not is_tech:
        return redirect('login')

    appointments = Appointment.objects.all().select_related('patient', 'test').order_by('-appointment_date')

    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

    if status_filter in ('Pending', 'Completed', 'Cancelled'):
        appointments = appointments.filter(status=status_filter)

    if search_query:
        appointments = appointments.filter(patient__username__icontains=search_query)

    today = timezone.localdate()

    pending_count = Appointment.objects.filter(status='Pending').count()
    completed_today_count = Appointment.objects.filter(
        status='Completed', completed_at__date=today
    ).count()
    cancelled_count = Appointment.objects.filter(status='Cancelled').count()
    total_patients = Appointment.objects.values('patient').distinct().count()

    # Live queue: pending appointments waiting to be processed, soonest first.
    active_queue = (
        Appointment.objects.filter(status='Pending')
        .select_related('patient', 'test')
        .order_by('appointment_date')[:8]
    )

    # Most recently completed sessions, for a quick activity feed.
    recent_completed = (
        Appointment.objects.filter(status='Completed')
        .select_related('patient', 'test')
        .order_by('-appointment_date')[:5]
    )

    # Test-volume breakdown so staff can see what's driving demand.
    test_breakdown_qs = (
        Appointment.objects.values('test__test_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    max_breakdown_count = max([row['count'] for row in test_breakdown_qs], default=0)
    test_breakdown = [
        {
            'name': row['test__test_name'],
            'count': row['count'],
            'percent': round((row['count'] / max_breakdown_count) * 100) if max_breakdown_count else 0,
        }
        for row in test_breakdown_qs
    ]

    return render(request, 'laboratory/technician.html', {
        'appointments': appointments,
        'pending_count': pending_count,
        'completed_count': Appointment.objects.filter(status='Completed').count(),
        'completed_today_count': completed_today_count,
        'cancelled_count': cancelled_count,
        'total_patients': total_patients,
        'active_queue': active_queue,
        'recent_completed': recent_completed,
        'test_breakdown': test_breakdown,
        'status_filter': status_filter,
        'search_query': search_query,
        'today': today,
    })


def _is_admin(user):
    """
    True for accounts flagged with the 'admin' role, plus superusers
    (so the Django-created superuser account can reach the professional
    Admin Dashboard without needing its role field hand-edited).
    Technicians are intentionally excluded even if a technician account
    happens to also be a superuser -- see login_view routing.
    """
    is_tech = (hasattr(user, 'role') and user.role == 'technician') or user.username == 'tech'
    if is_tech:
        return False
    return (hasattr(user, 'role') and user.role == 'admin') or user.is_superuser


@login_required
def admin_dashboard_view(request):
    """
    Professional Admin Command Center -- a real dashboard (matching the
    look of the patient/technician workspaces) instead of the raw Django
    admin, giving administrators a single-glance operational overview:
    patient/technician headcounts, revenue collected, and workflow
    status across every appointment in the system.
    """
    if not _is_admin(request.user):
        messages.error(request, "Access restricted to authorized administrator profiles.")
        return redirect('login')

    User = get_user_model()

    total_patients = User.objects.filter(role='patient').count()
    total_technicians = User.objects.filter(role='technician').count()

    appointments = Appointment.objects.select_related('patient', 'test')

    pending_count = appointments.filter(status='Pending').count()
    completed_count = appointments.filter(status='Completed').count()
    cancelled_count = appointments.filter(status='Cancelled').count()
    total_bookings = appointments.count()

    total_payment = appointments.filter(status='Completed').aggregate(
        total=Sum('test__price')
    )['total'] or 0
    pending_payment = appointments.filter(status='Pending').aggregate(
        total=Sum('test__price')
    )['total'] or 0

    today = timezone.localdate()
    today_payment = appointments.filter(
        status='Completed', completed_at__date=today
    ).aggregate(total=Sum('test__price'))['total'] or 0

    recent_patients = User.objects.filter(role='patient').order_by('-date_joined')[:5]
    recent_technicians = User.objects.filter(role='technician').order_by('-date_joined')[:5]
    recent_activity = appointments.order_by('-appointment_date')[:8]

    can_open_django_admin = request.user.is_staff or request.user.is_superuser

    return render(request, 'laboratory/admin_dashboard.html', {
        'total_patients': total_patients,
        'total_technicians': total_technicians,
        'total_bookings': total_bookings,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'total_payment': total_payment,
        'pending_payment': pending_payment,
        'today_payment': today_payment,
        'recent_patients': recent_patients,
        'recent_technicians': recent_technicians,
        'recent_activity': recent_activity,
        'can_open_django_admin': can_open_django_admin,
        'today': today,
    })


@login_required
def admin_patient_records_view(request):
    """
    Dedicated, searchable roster of every patient account, with a
    quick appointment count per patient.
    """
    if not _is_admin(request.user):
        messages.error(request, "Access restricted to authorized administrator profiles.")
        return redirect('login')

    User = get_user_model()
    search_query = request.GET.get('q', '').strip()

    patients = User.objects.filter(role='patient').order_by('-date_joined')
    if search_query:
        patients = patients.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(full_name__icontains=search_query)
        )
    patients = patients.annotate(appointment_count=Count('appointments'))

    return render(request, 'laboratory/admin_patient_records.html', {
        'patients': patients,
        'search_query': search_query,
        'total_patients': User.objects.filter(role='patient').count(),
    })


@login_required
def admin_technician_records_view(request):
    """
    Dedicated, searchable roster of every technician account, with a
    quick count of how many results each has verified/signed off.
    """
    if not _is_admin(request.user):
        messages.error(request, "Access restricted to authorized administrator profiles.")
        return redirect('login')

    User = get_user_model()
    search_query = request.GET.get('q', '').strip()

    technicians = User.objects.filter(role='technician').order_by('-date_joined')
    if search_query:
        technicians = technicians.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(full_name__icontains=search_query)
        )
    technicians = technicians.annotate(verified_count=Count('verified_results', distinct=True))

    return render(request, 'laboratory/admin_technician_records.html', {
        'technicians': technicians,
        'search_query': search_query,
        'total_technicians': User.objects.filter(role='technician').count(),
    })


@login_required
def admin_add_technician_view(request):
    """
    Lets an administrator create technician accounts from inside the
    app (instead of the raw Django admin), with a system-generated
    username and a password that must pass the same strong-password
    rules as everyone else -- so accounts no longer get set up with
    something like 'test' / '123'.
    """
    if not _is_admin(request.user):
        messages.error(request, "Access restricted to authorized administrator profiles.")
        return redirect('login')

    User = get_user_model()
    suggested_username = ''
    suggested_password = generate_strong_temp_password()
    full_name = ''
    email = ''
    phone = ''

    if request.method == 'POST':
        full_name = (request.POST.get('full_name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        password = request.POST.get('password') or ''
        confirm_password = request.POST.get('confirm_password') or ''
        suggested_username = generate_unique_username(full_name, role_prefix='tech')

        # Whatever the admin already typed, keep it on screen if a check
        # below fails -- only the password fields are left out (they're
        # never echoed back into the HTML on error).
        form_data = {
            'suggested_username': suggested_username,
            'suggested_password': suggested_password,
            'full_name': full_name,
            'email': email,
            'phone': phone,
        }

        if not full_name or not email:
            messages.error(request, "Full name and email are required.")
            return render(request, 'laboratory/admin_add_technician.html', form_data)

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'laboratory/admin_add_technician.html', form_data)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'laboratory/admin_add_technician.html', form_data)

        try:
            validate_password(password)
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
            form_data['suggested_password'] = generate_strong_temp_password()
            return render(request, 'laboratory/admin_add_technician.html', form_data)

        username = generate_unique_username(full_name, role_prefix='tech')
        tech = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            password=password,
            role='technician',
        )
        name_parts = full_name.split(' ', 1)
        tech.first_name = name_parts[0]
        tech.last_name = name_parts[1] if len(name_parts) > 1 else ''
        tech.full_name = full_name
        tech.save()

        messages.success(
            request,
            f"Technician account created. Username: {username}"
        )
        return redirect('admin_technician_records')

    return render(request, 'laboratory/admin_add_technician.html', {
        'suggested_username': suggested_username,
        'suggested_password': suggested_password,
        'full_name': full_name,
        'email': email,
        'phone': phone,
    })


@login_required
def admin_edit_technician_view(request, technician_id):
    """
    Lets an administrator update a single technician's profile details,
    reactivate/suspend their access, and reset their password -- all
    subject to the same strong-password validation as account creation.
    """
    if not _is_admin(request.user):
        messages.error(request, "Access restricted to authorized administrator profiles.")
        return redirect('login')

    User = get_user_model()
    tech = get_object_or_404(User, id=technician_id, role='technician')

    if request.method == 'POST':
        full_name = (request.POST.get('full_name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        is_active = request.POST.get('is_active') == 'on'
        new_password = request.POST.get('new_password') or ''
        confirm_password = request.POST.get('confirm_password') or ''

        # Apply the submitted values to the in-memory object right away,
        # before any validation -- so if a check below fails, the form
        # redisplays what the admin just typed instead of the old saved
        # values. tech.save() still only happens after every check passes.
        if full_name:
            name_parts = full_name.split(' ', 1)
            tech.first_name = name_parts[0]
            tech.last_name = name_parts[1] if len(name_parts) > 1 else ''
            tech.full_name = full_name
        tech.email = email
        tech.phone = phone
        tech.is_active = is_active

        if email and User.objects.filter(email=email).exclude(id=tech.id).exists():
            messages.error(request, "Another account already uses this email.")
            return render(request, 'laboratory/admin_edit_technician.html', {'tech': tech})

        if new_password or confirm_password:
            if new_password != confirm_password:
                messages.error(request, "The new passwords do not match.")
                return render(request, 'laboratory/admin_edit_technician.html', {'tech': tech})
            try:
                validate_password(new_password, user=tech)
            except ValidationError as e:
                for err in e.messages:
                    messages.error(request, err)
                return render(request, 'laboratory/admin_edit_technician.html', {'tech': tech})
            tech.set_password(new_password)

        tech.save()
        messages.success(request, "Technician account updated successfully.")
        return redirect('admin_technician_records')

    return render(request, 'laboratory/admin_edit_technician.html', {'tech': tech})


@login_required
def view_test_requests(request):
    """
    Dedicated standalone page listing test requests for technicians/admins.
    """
    is_tech = (
        (hasattr(request.user, 'role') and request.user.role in ['admin', 'technician'])
        or request.user.username == 'tech'
        or request.user.is_superuser
    )
    if not is_tech:
        messages.error(request, "Access restricted to authorized management profiles.")
        return redirect('dashboard')

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    appointments = Appointment.objects.all().select_related('patient', 'test').order_by('-appointment_date')

    if status_filter in ('Pending', 'Completed', 'Cancelled'):
        appointments = appointments.filter(status=status_filter)

    if search_query:
        appointments = appointments.filter(patient__username__icontains=search_query)

    return render(request, 'laboratory/test_requests.html', {
        'test_requests': appointments,
        'search_query': search_query,
        'status_filter': status_filter,
    })


# =========================================================================
# PROFILE CONFIGURATIONS & SETTINGS MANAGEMENT
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


@login_required
def generate_report_view(request, appointment_id):
    is_staff = (
        (hasattr(request.user, 'role') and request.user.role in ['admin', 'technician'])
        or request.user.username == 'tech'
        or request.user.is_superuser
    )
    if not is_staff:
        messages.error(request, "Access restricted to authorized management profiles.")
        return redirect('dashboard')

    appointment = get_object_or_404(Appointment, id=appointment_id)
    result = TestResult.objects.filter(appointment=appointment).first()

    if not result:
        result = TestResult(appointment=appointment)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit':
            result_value = request.POST.get('result_value')
            remarks = request.POST.get('remarks')

            if not result_value:
                messages.error(request, "Result value cannot be empty.")
                # Show what was typed instead of redirecting back to a
                # fresh GET, which would silently drop the remarks text
                # (and any result_value) the technician had already entered.
                result.result_value = result_value
                result.remarks = remarks
                return render(request, 'laboratory/generate_report.html', {
                    'appointment': appointment,
                    'result': result,
                    'patient_snapshot': _resolve_patient_snapshot(appointment),
                })

            result.result_value = result_value
            result.remarks = remarks
            result.updated_by = request.user
            result.verified = False
            result.verified_by = None
            result.verified_at = None
            result.save()

            appointment.status = 'Completed'
            # Only stamp completed_at the FIRST time a result is entered for
            # this appointment. This is the moment the test is actually
            # finished and payment is effectively collected -- it must not
            # be overwritten by a later correction/edit to the result, or
            # revenue would silently shift to whatever day someone later
            # fixes a typo in the result.
            if appointment.completed_at is None:
                appointment.completed_at = timezone.now()
            appointment.save()
            messages.success(request, "Result saved. Please verify before uploading the final report.")

        elif action == 'verify':
            if not result.pk:
                messages.error(request, "Cannot verify -- no result has been entered yet.")
            else:
                result.verified = True
                result.verified_by = request.user
                result.verified_at = timezone.now()
                result.save()

                email_sent = _send_report_ready_email(appointment)
                if email_sent:
                    messages.success(request, "Result verified and report emailed to the patient.")
                else:
                    messages.success(request, "Result marked as verified.")
                    messages.warning(request, "Could not email the patient (no address on file or delivery failed).")

        return redirect('reports_list')

    return render(request, 'laboratory/generate_report.html', {
        'appointment': appointment,
        'result': result,
        'patient_snapshot': _resolve_patient_snapshot(appointment),
    })


# =========================================================================
# SECURE REPORT DOCUMENT STREAM DISTRIBUTION
# =========================================================================

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
            f'<font color="white" size="13"><b>#LMS-00{appointment.id}</b></font>',
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
    results_row = [
        Paragraph(_pdf_safe(test_name), cell_style),
        Paragraph(f"<b>{_pdf_safe(result_value)}</b>", cell_bold_style),
        Paragraph(_pdf_safe(unit), cell_style),
        Paragraph(_pdf_safe(normal_range), cell_style),
        Paragraph(flag_html, cell_style),
    ]
    results_table = Table(
        [results_header, results_row],
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
    story.append(Spacer(1, 8))
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


@login_required
def download_report_view(request, appointment_id):
    is_staff = (
        (hasattr(request.user, 'role') and request.user.role in ['admin', 'technician'])
        or request.user.username == 'tech'
        or request.user.is_superuser
    )

    if is_staff:
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
# AUTOMATED "REPORT READY" EMAIL NOTIFICATION
# =========================================================================

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


@login_required
def reports_list(request):
    appointments = Appointment.objects.filter(status='Completed').select_related('patient', 'test').order_by('-appointment_date')
    return render(request, 'laboratory/report_list.html', {'appointments': appointments})


@login_required
def admin_reports_list(request):
    """
    Dedicated, read-only "All Reports" page for administrators -- a
    simpler view of every completed report and its sign-off status,
    styled to match the rest of the admin dashboard instead of
    reusing the technician's "Generate Reports" workspace.
    """
    if not _is_admin(request.user):
        messages.error(request, "Access restricted to authorized administrator profiles.")
        return redirect('login')

    search_query = request.GET.get('q', '').strip()

    appointments = Appointment.objects.filter(status='Completed').select_related(
        'patient', 'test', 'result'
    ).order_by('-appointment_date')

    if search_query:
        appointments = appointments.filter(
            Q(patient__username__icontains=search_query)
            | Q(patient__full_name__icontains=search_query)
            | Q(patient__email__icontains=search_query)
        )

    can_open_django_admin = request.user.is_staff or request.user.is_superuser

    return render(request, 'laboratory/admin_report_list.html', {
        'appointments': appointments,
        'search_query': search_query,
        'can_open_django_admin': can_open_django_admin,
    })
