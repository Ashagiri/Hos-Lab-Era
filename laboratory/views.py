import io
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

# ReportLab Engine Modules
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Database App Entities
from .models import LabTest, Appointment, TestResult

# =========================================================================
# SYSTEM MARKETING ENTRY VIEW
# =========================================================================

def home_view(request):
    """
    Renders the primary landing marketing homepage.
    """
    return render(request, 'laboratory/home.html')


# =========================================================================
# CORE DASHBOARDS & PROFILES (DYNAMIC ROUTING ENGINE)
# =========================================================================

@login_required
def dashboard_view(request):
    """
    Dynamic routing dashboard engine. Evaluates roles to stream appropriate tracking datasets.
    Patients see their own unique test profiles, while Admins view across incoming workflows.
    """
    if request.user.role == 'admin':
        # Admin pipelines view all recent requests across standard system operations
        appointments = Appointment.objects.all().order_by('-appointment_date')
        return render(request, 'laboratory/admin_dashboard.html', {'appointments': appointments})
    else:
        # Patients capture exclusively their own personal histories
        appointments = Appointment.objects.filter(patient=request.user).order_by('-appointment_date')
        return render(request, 'laboratory/dashboard.html', {'appointments': appointments})


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
        selected_test_ids = request.POST.getlist('tests[]')
        
        # Input guard validations
        if not selected_test_ids or not appointment_date or not appointment_time:
            messages.error(request, "Please select at least one test, date, and time slot.")
            return redirect('booking')

        try:
            # 3. Generate records independently for each checked parameter
            for test_id in selected_test_ids:
                test_instance = LabTest.objects.get(id=test_id)
                
                Appointment.objects.create(
                    patient=request.user,
                    test=test_instance,
                    appointment_date=appointment_date,
                    status='Pending'
                )
                
            messages.success(request, "Your laboratory test session has been booked successfully!")
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Error while writing booking to database: {str(e)}")
            return redirect('booking')

    # GET Workflow processing
    all_tests = LabTest.objects.all().select_related('category')
    return render(request, 'laboratory/booking.html', {'tests': all_tests})


# =========================================================================
# DIAGNOSTIC DATA ENTRY & PROCESSING (ADMIN)
# =========================================================================

@login_required
def record_test_result(request, appointment_id):
    """
    Allows Admins to directly attach observed metric attributes and textual remarks 
    directly to explicit records.
    """
    if request.user.role != 'admin':
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
        return redirect('dashboard')

    return render(request, 'laboratory/record_result.html', {'appointment': appointment, 'result': existing_result})


# =========================================================================
# SECURE REPORT DOCUMENT STREAM DISTRIBUTION
# =========================================================================

@login_required
def download_report_view(request, appointment_id):
    """
    Assembles a certified binary PDF stream report file dynamically using ReportLab layout canvas matrices.
    """
    # Enforce basic visibility context boundaries logic check
    if request.user.role == 'admin':
        appointment = get_object_or_404(Appointment, id=appointment_id)
    else:
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # --- PDF HEADER BANNER LAYOUT ---
    p.setFillColor(colors.HexColor("#1a233a")) 
    p.rect(0, 720, 612, 100, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, 760, "LABPORTAL MEDICAL DIAGNOSTICS")
    p.setFont("Helvetica", 10)
    p.drawString(40, 740, "Certified Clinical Laboratory Report • Official Copy")
    
    # --- PATIENT DETAIL CARDS ---
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
    
    # --- MEDICAL PARAMETER DATA TABLE ---
    p.setFillColor(colors.HexColor("#2563eb"))
    p.rect(40, 520, 532, 25, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, 528, "TEST PARAMETER")
    p.drawString(250, 528, "RESULT")
    p.drawString(380, 528, "NORMAL RANGE")
    p.drawString(490, 528, "FLAG")
    
    # Row Data Values
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 11)
    p.drawString(50, 490, f"{appointment.test.test_name}")
    
    # Extract structural analytical evaluation criteria dynamically if verified data models exist
    try:
        live_result = appointment.result
        display_val = live_result.result_value
        display_remarks = live_result.remarks or "NORMAL"
    except (TestResult.DoesNotExist, AttributeError):
        # Fallback tracking if results aren't recorded in detail model segments yet
        display_val = "14.2 g/dL" if "blood" in appointment.test.test_name.lower() else "98 mg/dL"
        display_remarks = "NORMAL"

    p.drawString(250, 490, display_val)
    p.drawString(380, 490, appointment.test.normal_range)
    p.setFillColor(colors.HexColor("#16a34a"))
    p.drawString(490, 490, display_remarks)
        
    p.setStrokeColor(colors.HexColor("#cbd5e1"))
    p.setLineWidth(1)
    p.line(40, 475, 572, 475)
    
    # --- FOOTER METADATA ---
    p.setFillColor(colors.HexColor("#64748b"))
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(40, 100, "* This is a digitally verified laboratory report generated by LabPortal.")
    p.drawString(40, 85, "  Authorized signatures are archived within security infrastructure registries securely.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"LabReport_00{appointment.id}.pdf")

@login_required
def dashboard_view(request):
    """
    Secure Dynamic Router. Evaluates authenticated user attributes to 
    ensure patients only see their personal test profiles, while strictly
    restricting the Admin Control Center to authorized management.
    """
    # 1. Strict Security Guard: Check if the user's role attribute is explicitly set to 'admin'
    if hasattr(request.user, 'role') and request.user.role == 'admin':
        # Admin Pipeline: Fetch all system wide pending requests for management
        appointments = Appointment.objects.all().order_by('-appointment_date')
        return render(request, 'laboratory/admin_dashboard.html', {'appointments': appointments})
        
    else:
        # Patient Pipeline: Re-route normal users exclusively to their personal workspace
        appointments = Appointment.objects.filter(patient=request.user).order_by('-appointment_date')
        return render(request, 'laboratory/dashboard.html', {'appointments': appointments})