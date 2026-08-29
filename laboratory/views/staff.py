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
from accounts.decorators import is_technician, is_lab_staff, role_required


from ._common import _resolve_patient_snapshot, _send_report_ready_email

@role_required(is_lab_staff)
def technician_dashboard_view(request):
    """
    Technician Overview Dashboard.
    """
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

@role_required(is_lab_staff, redirect_to='dashboard')
def view_test_requests(request):
    """
    Dedicated standalone page listing test requests for technicians/admins.
    """
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

@role_required(is_lab_staff, redirect_to='dashboard')
def generate_report_view(request, appointment_id):
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

@role_required(is_lab_staff, redirect_to='dashboard')
def reports_list(request):
    """
    NOTE: this previously had no role check beyond @login_required --
    any authenticated patient could browse every OTHER patient's
    completed appointments (name, test, date) just by visiting this
    URL directly. Now gated the same as the rest of the staff area.
    """
    appointments = Appointment.objects.filter(status='Completed').select_related('patient', 'test').order_by('-appointment_date')
    return render(request, 'laboratory/report_list.html', {'appointments': appointments})

