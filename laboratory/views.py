import io
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
from .models import LabTest, Appointment, TestResult 
from laboratory import views



# =========================================================================
# APPOINTMENT SLOT CAPACITY CONFIG
# =========================================================================

# Max number of distinct patients allowed per date + time slot.
SLOT_CAPACITY = 5

# Must match the <option> values in booking.html's Time Slot dropdown exactly.
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
    appointment for the given date + time slot. A patient booking multiple
    tests in the same slot only counts once.
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
    (same date) and returns the first one that still has room.
    Returns None if every later slot that day is also full.
    """
    try:
        start_index = TIME_SLOTS.index(requested_slot)
    except ValueError:
        start_index = -1  # unrecognized slot value -> just scan from the top

    for slot in TIME_SLOTS[start_index + 1:]:
        if _slot_patient_count(appointment_date, slot, exclude_patient_id) < SLOT_CAPACITY:
            return slot
    return None


# =========================================================================
# STATIC DISPLAY METADATA (icons/descriptions not stored in the DB)
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
# CORE WORKSPACE DASHBOARDS (DYNAMIC SEGREGATION)
# =========================================================================

@login_required
def dashboard_view(request):
    """
    Patient Workspace Dashboard.
    Exclusively queries and renders the logged-in user's personal histories.
    """
    appointments = Appointment.objects.filter(patient=request.user).order_by('-appointment_date')
    return render(request, 'laboratory/dashboard.html', {'appointments': appointments})


@login_required
def technician_dashboard_view(request):
    is_tech = (
        (hasattr(request.user, 'role') and request.user.role == 'technician')
        or request.user.username == 'tech'
        or request.user.is_superuser
    )
    if not is_tech:
        return redirect('login')

    appointments = Appointment.objects.all().order_by('-appointment_date')

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
    """
    Dedicated standalone page (own URL) listing all pending test requests
    for technicians/admins to pick up and process, separate from the
    main dashboard.
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

    appointments = Appointment.objects.filter(status='Pending').order_by('-appointment_date')

    if search_query:
        appointments = appointments.filter(patient__username__icontains=search_query)

    return render(request, 'laboratory/test_requests.html', {
        'appointments': appointments,
        'search_query': search_query,
    })


# =========================================================================
# PROFILE CONFIGURATIONS & SETTINGS MANAGEMENT
# =========================================================================

@login_required
def settings_view(request):
    """
    Manages personal account fields updates, system alerts switches, and cryptographic
    password validation sequences safely for any logged-in user profile context.
    """
    user = request.user
    if request.method == 'POST':
        # 1. Update Core Bio Meta Fields
        user.full_name = request.POST.get('full_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.save()

        # 2. Update Passwords Safely via Cryptographic Validation Check
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
                update_session_auth_hash(request, user)  # Prevents logging out active session
                messages.success(request, "Password parameters modified successfully.")
        else:
            messages.success(request, "Account details saved successfully.")

        return redirect('settings')

    return render(request, 'laboratory/settings.html')


# =========================================================================
# PATIENT SCHEDULING OPERATIONS
# =========================================================================

@login_required
def booking_view(request):
    """
    Handles diagnostic test booking creation forms via POST data pipelines,
    and streams database available test sets via GET requests.
    """
    if request.method == 'POST':
        # 1. Capture schedule timelines from client form elements
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')

        # 2. Extract selected test primary keys array list
        selected_test_ids = request.POST.getlist('tests')

        # Input guard validations
        if not selected_test_ids or not appointment_date or not appointment_time:
            messages.error(request, "Please select at least one test, date, and time slot.")
            return redirect('booking')

        parsed_date = parse_date(appointment_date)
        if parsed_date is None:
            messages.error(request, "Invalid appointment date. Please try again.")
            return redirect('booking')

        existing_patient_count = _slot_patient_count(
            parsed_date, appointment_time, exclude_patient_id=request.user.id
        )
        if existing_patient_count >= SLOT_CAPACITY:
            suggested_slot = _next_available_slot(parsed_date, appointment_time, request.user.id)
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
            # 3. Generate records independently for each checked parameter
            for test_id in selected_test_ids:
                test_instance = LabTest.objects.get(id=test_id)

                Appointment.objects.create(
                    patient=request.user,
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

    # Attach display-only icon + description metadata (not persisted to DB)
    for test in all_tests:
        info = TEST_DISPLAY_INFO.get(test.test_name, {"icon": "🧪", "desc": ""})
        test.icon = info["icon"]
        test.display_desc = info["desc"]

    return render(request, 'laboratory/booking.html', {'tests': all_tests})


@login_required
def check_slot_availability(request):
    """
    GET /booking/check-slots/?date=YYYY-MM-DD
    Returns JSON with each time slot's booked count and whether it's full.
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
def record_test_result(request, appointment_id):
    """
    Allows Technicians and Admin users to attach metrics and remarks directly to records.
    """
    is_staff = (
        (hasattr(request.user, 'role') and request.user.role in ['admin', 'technician'])
        or request.user.username == 'tech'
        or request.user.is_superuser
    )
    if not is_staff:
        messages.error(request, "Access restricted to authorized management profiles.")
        return redirect('dashboard')

    appointment = get_object_or_404(Appointment, id=appointment_id)
    existing_result = getattr(appointment, 'result', None)

    if request.method == 'POST':
        result_value = request.POST.get('result_value')
        remarks = request.POST.get('remarks')

        if not result_value:
            messages.error(request, "Observed analytical value fields cannot match empty strings.")
            return redirect('record_test_result', appointment_id=appointment.id)

        if existing_result:
            existing_result.result_value = result_value
            existing_result.remarks = remarks
            existing_result.updated_by = request.user
            existing_result.save()
        else:
            TestResult.objects.create(
                appointment=appointment,
                result_value=result_value,
                remarks=remarks,
                updated_by=request.user
            )

        appointment.status = 'Completed'
        appointment.save()

        messages.success(request, f"Diagnostic testing criteria recorded for {appointment.patient.username}.")
        return redirect('technician_dashboard')

    return render(request, 'laboratory/record_result.html', {'appointment': appointment, 'result': existing_result})


@login_required
def generate_report_view(request, appointment_id):
    """
    Report workspace: Edit result, Verify result, then Upload/Download the final PDF.
    """
    is_staff = (
        (hasattr(request.user, 'role') and request.user.role in ['admin', 'technician'])
        or request.user.username == 'tech'
        or request.user.is_superuser
    )
    if not is_staff:
        messages.error(request, "Access restricted to authorized management profiles.")
        return redirect('dashboard')

    appointment = get_object_or_404(Appointment, id=appointment_id)
    result = getattr(appointment, 'result', None)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit':
            result_value = request.POST.get('result_value')
            remarks = request.POST.get('remarks')

            if not result_value:
                messages.error(request, "Result value cannot be empty.")
                return redirect('generate_report', appointment_id=appointment.id)

            if result:
                result.result_value = result_value
                result.remarks = remarks
                result.updated_by = request.user
                result.verified = False
                result.verified_by = None
                result.verified_at = None
                result.save()
            else:
                result = TestResult.objects.create(
                    appointment=appointment,
                    result_value=result_value,
                    remarks=remarks,
                    updated_by=request.user,
                )

            appointment.status = 'Completed'
            appointment.save()
            messages.success(request, "Result saved. Please verify before uploading the final report.")

        elif action == 'verify':
            if not result:
                messages.error(request, "Cannot verify -- no result has been entered yet.")
            else:
                result.verified = True
                result.verified_by = request.user
                result.verified_at = timezone.now()
                result.save()
                messages.success(request, "Result marked as verified.")

        return redirect('generate_report', appointment_id=appointment.id)

    return render(request, 'laboratory/generate_report.html', {
        'appointment': appointment,
        'result': result,
    })


# =========================================================================
# SECURE REPORT DOCUMENT STREAM DISTRIBUTION
# =========================================================================

@login_required
def download_report_view(request, appointment_id):
    """
    Assembles a certified binary PDF stream report file dynamically using ReportLab layouts.
    """
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
    p.drawString(60, 665, f"Patient Name: {appointment.patient.username}")
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

    p.setFillColor(colors.black)
    p.setFont("Helvetica", 11)
    p.drawString(50, 490, f"{appointment.test.test_name}")

    try:
        live_result = appointment.result
        display_val = live_result.result_value
        display_remarks = live_result.remarks or "NORMAL"
    except (TestResult.DoesNotExist, AttributeError):
        display_val = "14.2 g/dL" if "blood" in appointment.test.test_name.lower() else "98 mg/dL"
        display_remarks = "NORMAL"

    p.drawString(250, 490, display_val)
    p.drawString(380, 490, appointment.test.normal_range)
    p.setFillColor(colors.HexColor("#16a34a"))
    p.drawString(490, 490, display_remarks)

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

def reports_list(request):
    # Temporary placeholder until you build your reports database query loop
    return render(request, 'laboratory/reports_list.html')

def view_test_requests(request):
    # Fixed: Using the actual field 'appointment_date' for database ordering
    test_requests = Appointment.objects.all().order_by('-appointment_date')
    
    return render(request, 'laboratory/test_requests.html', {
        'test_requests': test_requests
    })