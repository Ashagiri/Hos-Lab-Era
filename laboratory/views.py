from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# This handles your primary landing dashboard page
def home_view(request):
    # FIXED: Added the 'laboratory/' folder prefix so Django can find it perfectly!
    return render(request, 'laboratory/home.html')

@login_required # <--- This line redirects unauthenticated users
def booking_view(request):
    return render(request, 'laboratory/booking.html')
    