from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import User  # This targets your custom User model

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'accounts/register.html')
            
        # Create user profile with a default 'Patient' role
        user = User.objects.create_user(username=username, phone=phone, password=password, role='Patient')
        login(request, user)
        return redirect('home')
        
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'accounts/login.html')