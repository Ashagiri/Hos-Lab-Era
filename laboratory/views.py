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
        # 1. Extract the patient details and appointment slots from the form
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        selected_test_ids = request.POST.getlist('tests[]')  # Gets list of checked test IDs
        
        # Doctor info (optional fields)
        doctor_name = request.POST.get('doctor_name', '')
        doctor_id = request.POST.get('doctor_id', '')

        if not selected_test_ids or not appointment_date or not appointment_time:
            messages.error(request, "Please select at least one test and a schedule slot.")
            return redirect('booking')

        try:
            # 2. Loop through each selected test and create an appointment record
            for test_id in selected_test_ids:
                test_instance = LabTest.objects.get(id=test_id)
                
                Appointment.objects.create(
                    patient=request.user,
                    test=test_instance,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    doctor_name=doctor_name,
                    doctor_id=doctor_id,
                    status='Pending'
                )
                
            messages.success(request, "Your lab tests have been booked successfully!")
            return redirect('home')  # Send them back home with a success message
            
        except Exception as e:
            messages.error(request, f"Error booking appointment: {str(e)}")
            return redirect('booking')

    # GET request: Load all your dynamic tests from the admin database into the page
    all_tests = LabTest.objects.all().select_related('category')
    return render(request, 'laboratory/booking.html', {'tests': all_tests})