from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class CustomUserAdmin(BaseUserAdmin):
    # 1. Clean column layout using our safe custom field
    list_display = (
        'username', 
        'full_name', 
        'assigned_role',  # Displays the clean dash layout safely
        'phone', 
        'email', 
        'gender', 
        'age', 
        'last_login',    
        'date_joined'    
    )
    
    # 2. Chronological reverse ordering (Newest users on top)
    ordering = ('-date_joined',)
    
    # 3. Interactive sidebar filters
    list_filter = ('role', 'gender', 'is_staff', 'date_joined')
    
    # 4. Search capabilities
    search_fields = ('username', 'email', 'full_name', 'phone')

    # 5. Form editing layout structures
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Profile Fields', {'fields': ('role', 'phone', 'full_name', 'dob', 'age', 'gender')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Profile Fields', {'fields': ('role', 'phone', 'full_name', 'dob', 'age', 'gender')}),
    )

    # 💡 Safe Role Evaluator (No complex overrides to break the routing)
    @admin.display(description='Role', ordering='role')
    def assigned_role(self, obj):
        # Rule A: If user has administrator flags, show Admin
        if obj.is_superuser or obj.is_staff or str(obj.role).lower() == 'admin':
            return 'Admin'
        
        # Rule B: If user is a technician staff member, show Technician
        elif str(obj.role).lower() == 'tech' or 'tech' in obj.username.lower():
            return 'Technician'
        
        # Rule C: Keep everything else looking spotless with a clean dash
        return '-'

# Register the model cleanly back into the system
admin.site.register(User, CustomUserAdmin)