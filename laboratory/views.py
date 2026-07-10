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
        test_id = request.POST.get('test_id')
        appointment_date = request.POST.get('appointment_date')
        
        if not test_id or not appointment_date:
            messages.error(request, "Please fill out all required fields.")
            return redirect('booking')
            
        try:
            # 1. Grab the specific test instance selected by the patient
            selected_test = LabTest.objects.get(id=test_id)
            
            # 2. Create and save the new booking into your database table
            Appointment.objects.create(
                patient=request.user,
                test=selected_test,
                appointment_date=appointment_date,
                status='Pending'
            )
            
            messages.success(request, f"Successfully booked your {selected_test.test_name} session!")
            return redirect('home') # Sends them back to home upon success
            
        except Exception as e:
            messages.error(request, f"Error saving booking: {str(e)}")
            return redirect('booking')

    # GET request: Show the booking page populated with your actual database tests
    all_tests = LabTest.objects.all().select_related('category')
    return render(request, 'laboratory/booking.html', {'tests': all_tests})
    