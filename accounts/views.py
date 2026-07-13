from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import User  # Targets your custom User model

def register_view(request):
    if request.method == 'POST':
        # 1. Extract inputs matching your UI fields exactly
        full_name = request.POST.get('full_name')
        dob = request.POST.get('dob')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # 2. Validation Checks
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'accounts/register.html')
            
        if email and User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'accounts/register.html')

        try:
            # 3. Create the user using the email as the core username
            user = User.objects.create_user(
                username=email, 
                email=email,
                phone=phone, 
                password=password, 
                role='Patient'
            )
            
            # 4. Save your application's extra custom fields dynamically
            if hasattr(user, 'full_name'): user.full_name = full_name
            if hasattr(user, 'dob') and dob: user.dob = dob
            if hasattr(user, 'age') and age: user.age = int(age)
            if hasattr(user, 'gender'): user.gender = gender
            
            user.save()

            # 5. Establish user session and route straight to user dashboard
            login(request, user)
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Registration error: {str(e)}")
            return render(request, 'accounts/register.html')
        
    return render(request, 'accounts/register.html')


def login_view(request):
    """
    Handles secure user authentication and dynamic role-based dashboard deployment.
    """
    if request.method == 'POST':
        # Safely grab whatever value was typed into the primary identification input field
        username_input = request.POST.get('email') or request.POST.get('username')
        password_input = request.POST.get('password')
        
        # Fallback Check: If user typed their email address directly, locate the literal username field
        if username_input and '@' in username_input:
            try:
                matched_user = User.objects.get(email=username_input)
                username_input = matched_user.username
            except User.DoesNotExist:
                pass

        # Authenticate the user profile against Django's registry engine
        user = authenticate(request, username=username_input, password=password_input)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            
            # 🔀 DYNAMIC ROLE ROUTING SEQUENCE
            if hasattr(user, 'role') and user.role == 'admin':
                return redirect('admin_dashboard')  # Sends technicians straight to LABADMIN PRO
            else:
                return redirect('dashboard')        # Sends normal patients to the standard space
                
        else:
            messages.error(request, "Invalid authentication credentials. Please try again.")
            return redirect('login')
            
    return render(request, 'accounts/login.html')