from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import User  # This targets your custom User model

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'accounts/register.html')
            
        # Create user profile with custom fields included
        user = User.objects.create_user(
            username=username, 
            email=email,
            phone=phone, 
            password=password, 
            role='Patient'
        )
        
        # Save additional profile details to your model if fields exist
        if hasattr(user, 'full_name'): user.full_name = full_name
        if hasattr(user, 'dob'): user.dob = dob
        if hasattr(user, 'age'): user.age = age
        if hasattr(user, 'gender'): user.gender = gender
        user.save()

        login(request, user)
        return redirect('home')
        
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Explicitly matches HTML input name
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'accounts/login.html')