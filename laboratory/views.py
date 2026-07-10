from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LabTest, Appointment # Ensure Appointment is in your laboratory/models.py

# This handles your primary landing dashboard page
def home_view(request):
    # FIXED: Added the 'laboratory/' folder prefix so Django can find it perfectly!
    return render(request, 'laboratory/home.html')

@login_required # <--- This line redirects unauthenticated users
def booking_view(request):
    return render(request, 'laboratory/booking.html')

@login_required
def booking_view(request):
    if request.method == 'POST':
        # 1. Capture the schedule dates and times from the form
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        
        # 2. Get the list of checkmarked test IDs chosen by the patient
        selected_test_ids = request.POST.getlist('tests[]')
        
        # 3. Collect doctor referral information (optional fields)
        doctor_name = request.POST.get('doctor_name', '')
        doctor_id = request.POST.get('doctor_id', '')

        # Quick validation guard check
        if not selected_test_ids or not appointment_date or not appointment_time:
            messages.error(request, "Please select at least one test, date, and time slot.")
            return redirect('booking')

        try:
            # 4. Loop through every selected checkmark and log an independent appointment record
            for test_id in selected_test_ids:
                test_instance = LabTest.objects.get(id=test_id)
                
                Appointment.objects.create(
                    patient=request.user,
                    test=test_instance,  # Linked directly to your 'test' field
                    appointment_date=appointment_date,
                    status='Pending'
                )
                
            messages.success(request, "Your laboratory test session has been booked successfully!")
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f"Error while writing booking to database: {str(e)}")
            return redirect('booking')

    # GET request: Load real dynamic tests down into section 3 of your form
    all_tests = LabTest.objects.all().select_related('category')
    return render(request, 'laboratory/booking.html', {'tests': all_tests})

@login_required
def dashboard_view(request):
    # Fetch the logged-in user's appointments from the database
    user_appointments = Appointment.objects.filter(patient=request.user).order_by('-appointment_date')
    
    return render(request, 'laboratory/dashboard.html', {
        'appointments': user_appointments
    })