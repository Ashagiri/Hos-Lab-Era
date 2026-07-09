from django.shortcuts import render
from django.http import HttpResponse

# This handles your primary landing dashboard page
def home_view(request):
    # FIXED: Added the 'laboratory/' folder prefix so Django can find it perfectly!
    return render(request, 'laboratory/home.html')
    