from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import User  # Targets your custom User model

def register_view(request):
    if request.method == 'POST':
        # 1. Extract inputs matching your UI fields exactly (image_d492f4.jpg)
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
            # This links the registration form (image_d492f4.jpg) with the login form (image_d495e1.jpg)
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

            # 5. Establish user session and route to homepage
            login(request, user)
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f"Registration error: {str(e)}")
            return render(request, 'accounts/register.html')
        
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        # Extracts what the user typed into the "Username" input box (image_d495e1.jpg)
        username = request.POST.get('username') 
        password = request.POST.get('password')
        
        # Authenticates the credentials using the email address stored as the username property
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'accounts/login.html')