import io
import re
import logging
from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse
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
from accounts.utils import generate_unique_username, generate_strong_temp_password
from accounts.decorators import is_admin, role_required


@role_required(is_admin)
def admin_dashboard_view(request):
    """
    Professional Admin Command Center -- a real dashboard (matching the
    look of the patient/technician workspaces) instead of the raw Django
    admin, giving administrators a single-glance operational overview:
    patient/technician headcounts, revenue collected, and workflow
    status across every appointment in the system.
    """
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

@role_required(is_admin)
def admin_patient_records_view(request):
    """
    Dedicated, searchable roster of every patient account, with a
    quick appointment count per patient.
    """
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

@role_required(is_admin)
def admin_technician_records_view(request):
    """
    Dedicated, searchable roster of every technician account, with a
    quick count of how many results each has verified/signed off.
    """
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

@role_required(is_admin)
def admin_add_technician_view(request):
    """
    Lets an administrator create technician accounts from inside the
    app (instead of the raw Django admin), with a system-generated
    username and a password that must pass the same strong-password
    rules as everyone else -- so accounts no longer get set up with
    something like 'test' / '123'.
    """
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

@role_required(is_admin)
def admin_edit_technician_view(request, technician_id):
    """
    Lets an administrator update a single technician's profile details,
    reactivate/suspend their access, and reset their password -- all
    subject to the same strong-password validation as account creation.
    """
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

@role_required(is_admin)
def admin_reports_list(request):
    """
    Dedicated, read-only "All Reports" page for administrators -- a
    simpler view of every completed report and its sign-off status,
    styled to match the rest of the admin dashboard instead of
    reusing the technician's "Generate Reports" workspace.
    """
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

