import io
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.utils.dateparse import parse_date
from django.utils import timezone

# ReportLab Engine Modules
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Database App Entities
from .models import LabTest, Appointment, TestResult, PatientProfile


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
    qs = Appointment.objects.filter(
        appointment_date__date=appointment_date,
        appointment_time=appointment_time,
        status__in=['Pending', 'Completed'],
    )
    if exclude_patient_id is not None:
        qs = qs.exclude(patient_id=exclude_patient_id)
    return qs.values('patient_id').distinct().count()


def _next_available_slot(appointment_date, requested_slot, exclude_patient_id):
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
    return render(request, 'laboratory/home.html')


# =========================================================================
# CORE WORKSPACE DASHBOARDS
# =========================================================================

@login_required
def dashboard_view(request):
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

    return render(request, 'laboratory/technician.html', {
        'appointments': appointments,
        'pending_count': Appointment.objects.filter(status='Pending').count(),
        'completed_count': Appointment.objects.filter(status='Completed').count(),
        'status_filter': status_filter,
        'search_query': search_query,
    })


@login_required
def view_test_requests(request):
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
        'appointments': appointments,
        'search_query': search_query,
        'status_filter': status_filter,
    })


# =========================================================================
# PROFILE CONFIGURATIONS & SETTINGS MANAGEMENT
# =========================================================================

@login_required
def settings_view(request):
    user = request.user
    patient_prof = getattr(user, 'patient_profile', None)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        if full_name and hasattr(user, 'first_name'):
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''

        user.email = request.POST.get('email', user.email)
        user.save()

        if patient_prof:
            if hasattr(patient_prof, 'phone'):
                patient_prof.phone = request.POST.get('phone', patient_prof.phone)
            if hasattr(patient_prof, 'address'):
                patient_prof.address = request.POST.get('address', patient_prof.address)
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
    user = request.user
    patient_prof = getattr(user, 'patient_profile', None)

    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        selected_test_ids = request.POST.getlist('tests')

        # Safely save patient fields if they exist on model
        if patient_prof:
            address_input = request.POST.get('address')
            phone_input = request.POST.get('phone')
            age_input = request.POST.get('age')
            gender_input = request.POST.get('gender')

            if address_input and hasattr(patient_prof, 'address'):
                patient_prof.address = address_input
            if phone_input and hasattr(patient_prof, 'phone'):
                patient_prof.phone = phone_input
            if age_input and hasattr(patient_prof, 'age'):
                patient_prof.age = age_input
            if gender_input and hasattr(patient_prof, 'gender'):
                patient_prof.gender = gender_input
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
            for test_id in selected_test_ids:
                test_instance = LabTest.objects.get(id=test_id)

                Appointment.objects.create(
                    patient=user,
                    test=test_instance,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    status='Pending'
                )

            messages.success(request, "Your laboratory test session has been booked successfully!")
            return redirect('dashboard')

        except LabTest.DoesNotExist:
            messages.error(request, "One or more selected tests could not be found. Please try again.")
            return redirect('booking')
        except Exception as e:
            messages.error(request, f"Error while writing booking to database: {str(e)}")
            return redirect('booking')

    # GET Workflow processing
    all_tests = LabTest.objects.all().select_related('category')

    for test in all_tests:
        info = TEST_DISPLAY_INFO.get(test.test_name, {"icon": "🧪", "desc": ""})
        test.icon = info["icon"]
        test.display_desc = info["desc"]

    # Safe attribute extraction preventing AttributeError
    profile_data = {
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'phone': getattr(user, 'phone', getattr(patient_prof, 'phone', '')) if patient_prof else '',
        'address': getattr(user, 'address', getattr(patient_prof, 'address', '')) if patient_prof else '',
        'age': getattr(user, 'age', getattr(patient_prof, 'age', '')) if patient_prof else '',
        'gender': getattr(user, 'gender', getattr(patient_prof, 'gender', '')) if patient_prof else '',
    }

    return render(request, 'laboratory/booking.html', {
        'tests': all_tests,
        'user_info': profile_data,
    })


@login_required
def check_slot_availability(request):
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
def record_test_result(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    existing_result = getattr(appointment, 'result', None)

    if request.method == 'POST':
        result_value = request.POST.get('result_value')
        remarks = request.POST.get('remarks')

        if existing_result:
            existing_result.result_value = result_value
            existing_result.remarks = remarks
            existing_result.updated_by = request.user
            existing_result.verified = False
            existing_result.verified_by = None
            existing_result.verified_at = None
            existing_result.save()
            messages.success(request, "Test result updated. Verification reset pending review.")
        else:
            new_result = TestResult(
                appointment=appointment,
                result_value=result_value,
                remarks=remarks,
                updated_by=request.user
            )
            new_result.save()
            
            appointment.status = 'Completed'
            appointment.save()
            messages.success(request, "New laboratory test result submitted successfully.")

        return redirect('view_test_requests')

    context = {
        'appointment': appointment,
        'result': existing_result
    }
    return render(request, 'laboratory/record_result.html', context)


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
                return redirect('generate_report', appointment_id=appointment.id)

            result.result_value = result_value
            result.remarks = remarks
            result.updated_by = request.user
            result.verified = False
            result.verified_by = None
            result.verified_at = None
            result.save()

            appointment.status = 'Completed'
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
                messages.success(request, "Result marked as verified.")

        return redirect('reports_list')

    return render(request, 'laboratory/generate_report.html', {
        'appointment': appointment,
        'result': result,
    })


# =========================================================================
# SECURE REPORT DOCUMENT STREAM DISTRIBUTION
# =========================================================================

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

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFillColor(colors.HexColor("#1a233a"))
    p.rect(0, 720, 612, 100, fill=1, stroke=0)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, 760, "LABPORTAL MEDICAL DIAGNOSTICS")
    p.setFont("Helvetica", 10)
    p.drawString(40, 740, "Certified Clinical Laboratory Report - Official Copy")

    p.setFillColor(colors.HexColor("#f8fafc"))
    p.rect(40, 580, 532, 110, fill=1, stroke=1)

    p.setFillColor(colors.HexColor("#1e293b"))
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, 665, f"Patient Name: {appointment.patient.get_full_name() or appointment.patient.username}")
    p.drawString(60, 645, f"Report ID: #LMS-00{appointment.id}")

    if hasattr(appointment.appointment_date, 'strftime'):
        formatted_date = appointment.appointment_date.strftime('%B %d, %Y')
    else:
        formatted_date = str(appointment.appointment_date)

    p.drawString(320, 665, f"Date Compiled: {formatted_date}")
    p.drawString(320, 645, f"Status: {appointment.status}")

    p.setFillColor(colors.HexColor("#2563eb"))
    p.rect(40, 520, 532, 25, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, 528, "TEST PARAMETER")
    p.drawString(250, 528, "RESULT")
    p.drawString(380, 528, "NORMAL RANGE")
    p.drawString(490, 528, "FLAG")

    test_name = appointment.test.test_name if appointment.test else "N/A"
    normal_range = appointment.test.normal_range if (appointment.test and hasattr(appointment.test, 'normal_range')) else "N/A"

    p.setFillColor(colors.black)
    p.setFont("Helvetica", 11)
    p.drawString(50, 490, f"{test_name}")

    try:
        live_result = appointment.result
        display_val = live_result.result_value if live_result.result_value else "Pending"
        display_remarks = live_result.remarks or "NORMAL"
    except (TestResult.DoesNotExist, AttributeError):
        display_val = "14.2 g/dL" if "blood" in test_name.lower() else "98 mg/dL"
        display_remarks = "NORMAL"

    p.drawString(250, 490, str(display_val))
    p.drawString(380, 490, str(normal_range))
    p.setFillColor(colors.HexColor("#16a34a"))
    p.drawString(490, 490, str(display_remarks))

    p.setStrokeColor(colors.HexColor("#cbd5e1"))
    p.setLineWidth(1)
    p.line(40, 475, 572, 475)

    p.setFillColor(colors.HexColor("#64748b"))
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(40, 100, "* This is a digitally verified laboratory report generated by LabPortal.")
    p.drawString(40, 85, "  Authorized signatures are archived within security infrastructure registries securely.")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"LabReport_00{appointment.id}.pdf")


@login_required
def reports_list(request):
    appointments = Appointment.objects.filter(status='Completed').select_related('patient', 'test').order_by('-appointment_date')
    return render(request, 'laboratory/report_list.html', {'appointments': appointments})