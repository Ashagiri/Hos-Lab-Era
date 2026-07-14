from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class CustomUserAdmin(BaseUserAdmin):
    # 1. CHANGED: Swap out the raw database 'role' field for our smart method 'assigned_role'
    list_display = (
        'username', 
        'full_name', 
        'assigned_role',  # Evaluates and shows the real role type cleanly
        'phone', 
        'email', 
        'gender', 
        'age', 
        'last_login',    
        'date_joined'    
    )
    
    # 2. CHRONOLOGICAL REVERSE ORDERING (Newest registered users at the top)
    ordering = ('-date_joined',)
    
    # 3. Interactive Sidebar Filters
    list_filter = ('role', 'gender', 'is_staff', 'date_joined')
    
    # 4. Global Search Fields
    search_fields = ('username', 'email', 'full_name', 'phone')

    # 5. Form editing layout rules
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Profile Fields', {'fields': ('role', 'phone', 'full_name', 'dob', 'age', 'gender')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Profile Fields', {'fields': ('role', 'phone', 'full_name', 'dob', 'age', 'gender')}),
    )

    # 💡 Smart Role Evaluator: Fixes the '123 showing as patient' issue automatically
    @admin.display(description='Role', ordering='role')
    def assigned_role(self, obj):
        # Rule A: If they have admin rights, they are an Admin (regardless of what the text field says)
        if obj.is_superuser or obj.is_staff or str(obj.role).lower() == 'admin':
            return 'Admin'
        # Rule B: If their username contains 'tech' or their role is 'tech', they are a Technician
        elif 'tech' in obj.username.lower() or str(obj.role).lower() == 'tech':
            return 'Technician'
        # Rule C: Default fallback for actual registered hospital clients
        return 'Patient'

# Register the stable configuration
admin.site.register(User, CustomUserAdmin)