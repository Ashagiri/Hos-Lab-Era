from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from laboratory.models import PatientProfile, Appointment  # Adjust to your exact model package locations

# Initialize the dynamic model lookup handle for your custom accounts.User swap
User = get_user_model()


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
            user = User.objects.create_user(
                username=email, 
                email=email,
                phone=phone, 
                password=password, 
                role='patient'
            )
            
            if hasattr(user, 'full_name'): user.full_name = full_name
            if hasattr(user, 'dob') and dob: user.dob = dob
            if hasattr(user, 'age') and age: user.age = int(age)
            if hasattr(user, 'gender'): user.gender = gender
            
            user.save()

            gender_map = {'male': 'M', 'female': 'F', 'other': 'O'}
            PatientProfile.objects.create(
                user=user,
                age=int(age) if age else 0,
                gender=gender_map.get((gender or '').lower(), 'O'),
            )

            # Registration complete — send them to login instead of auto-logging in
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f"Registration error: {str(e)}")
            return render(request, 'accounts/register.html')
        
    return render(request, 'accounts/register.html')


def login_view(request):
    """
    Handles secure user authentication and dynamic role-based dashboard deployment.
    Flushes pre-existing global dashboard or workflow messages on GET to keep the page contextual.
    """
    if request.method == 'POST':
        username_input = request.POST.get('email') or request.POST.get('username')
        password_input = request.POST.get('password')

        if not username_input or not password_input:
            messages.error(request, "Please enter both email/username and password.")
            return redirect('login')

        # Resolve email -> username if the user typed an email address
        lookup_input = username_input
        if '@' in username_input:
            try:
                matched_user = User.objects.get(email=username_input)
                lookup_input = matched_user.username
            except User.DoesNotExist:
                # No account with this email at all
                messages.error(
                    request,
                    "No account found with that email. Please create an account first."
                )
                return redirect('login')
        else:
            # Typed a username directly — check it exists before authenticating
            if not User.objects.filter(username=username_input).exists():
                messages.error(
                    request,
                    "No account found with that username. Please create an account first."
                )
                return redirect('login')

        # Account exists — now check the password
        user = authenticate(request, username=lookup_input, password=password_input)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")

            is_tech = (
                (hasattr(user, 'role') and user.role == 'technician')
                or user.username == 'tech'
                or user.is_superuser
            )
            if is_tech:
                return redirect('technician_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, "Incorrect password. Please try again.")
            return redirect('login')

    # ---> GET Request Handling: Clear out lingering background messages from other roles
    else:
        existing_messages = messages.get_messages(request)
        for _ in existing_messages:
            pass  # Iterating marks them all as seen
        existing_messages.used = True  # Flushes them completely out of storage

    return render(request, 'accounts/login.html')


def technician_login_view(request):
    """
    Dedicated authentication gateway exclusively for Technicians and Admin staff.
    """
    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')
        
        # Authenticate using the username and password provided in the form
        user = authenticate(request, username=username_input, password=password_input)
        
        if user is not None:
            is_tech_role = (
                (hasattr(user, 'role') and user.role == 'technician')
                or user.username == 'tech'
            )
            
            if is_tech_role or user.is_superuser:
                login(request, user)
                messages.success(request, "Technician Command Center Activated.")
                return redirect('technician_dashboard')
            else:
                messages.error(request, "Access Denied. You do not have technician privileges.")
                return redirect('technician_login')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('technician_login')
            
    return render(request, 'accounts/technician_login.html')


def logout_view(request):
    """
    Terminates the user session safely and returns the client to the splash index.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


def reports_list_view(request):
    appointments = Appointment.objects.select_related('patient', 'test').order_by('-appointment_date')
    return render(request, 'laboratory/reports_list_view.html', {'appointments': appointments})