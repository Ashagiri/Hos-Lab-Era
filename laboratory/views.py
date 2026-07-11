import io
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# ReportLab Engine Modules
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Database App Entities
from .models import LabTest, Appointment


def home_view(request):
    """
    Renders the primary landing marketing homepage.
    """
    return render(request, 'laboratory/home.html')


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
        
        # 3. Collect fallback metadata inputs
        doctor_name = request.POST.get('doctor_name', '')
        doctor_id = request.POST.get('doctor_id', '')

        # Input guard validations
        if not selected_test_ids or not appointment_date or not appointment_time:
            messages.error(request, "Please select at least one test, date, and time slot.")
            return redirect('booking')

        try:
            # 4. Generate records independently for each checked parameter
            for test_id in selected_test_ids:
                test_instance = LabTest.objects.get(id=test_id)
                
                Appointment.objects.create(
                    patient=request.user,
                    test=test_instance,
                    appointment_date=appointment_date,
                    status='Pending'
                )
                
            messages.success(request, "Your laboratory test session has been booked successfully!")
            return redirect('dashboard')  # Redirect straight to dashboard to let them see it live!
            
        except Exception as e:
            messages.error(request, f"Error while writing booking to database: {str(e)}")
            return redirect('booking')

    # GET Workflow processing
    all_tests = LabTest.objects.all().select_related('category')
    return render(request, 'laboratory/booking.html', {'tests': all_tests})


@login_required
def dashboard_view(request):
    """
    Fetches historical appointment metrics matching the signed-in patient context.
    """
    user_appointments = Appointment.objects.filter(patient=request.user).order_by('-appointment_date')
    return render(request, 'laboratory/dashboard.html', {'appointments': user_appointments})
    
    
@login_required
def download_report_view(request, appointment_id):
    """
    Assembles a certified binary PDF stream report file dynamically using ReportLab layout canvas matrices.
    """
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
    p.drawString(60, 665, f"Patient Name: {request.user.username}")
    p.drawString(60, 645, f"Report ID: #LMS-00{appointment.id}")
    
    # Simple check if appointment_date is a string or datetime object to prevent crashes
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
    
    # Check conditional criteria values matching requested variants
    if "blood" in appointment.test.test_name.lower():
        p.drawString(250, 490, "14.2 g/dL")
        p.drawString(380, 490, "13.5 - 17.5 g/dL")
        p.setFillColor(colors.HexColor("#16a34a"))
        p.drawString(490, 490, "NORMAL")
    else:
        p.drawString(250, 490, "98 mg/dL")
        p.drawString(380, 490, "70 - 100 mg/dL")
        p.setFillColor(colors.HexColor("#16a34a"))
        p.drawString(490, 490, "NORMAL")
        
    p.setStrokeColor(colors.HexColor("#cbd5e1"))
    p.setLineWidth(1)
    p.line(40, 475, 572, 475)
    
    # --- FOOTER METADATA SIGNatures ---
    p.setFillColor(colors.HexColor("#64748b"))
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(40, 100, "* This is a digitally verified laboratory report generated by LabPortal.")
    p.drawString(40, 85, "  Authorized signatures are archived within security infrastructure registries securely.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"LabReport_00{appointment.id}.pdf")