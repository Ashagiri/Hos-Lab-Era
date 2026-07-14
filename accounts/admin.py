from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class CustomUserAdmin(BaseUserAdmin):
    # 1. Clean column layout using safe custom fields
    list_display = (
        'username', 
        'full_name', 
        'assigned_role',  
        'phone', 
        'email', 
        'patient_gender',
        'patient_age',
        'last_login',    
        'date_joined'    
    )
    
    # 2. Chronological reverse ordering (Newest users on top)
    ordering = ('-date_joined',)
    
    # 3. Interactive sidebar filters (Filter on standard user properties)
    list_filter = ('role', 'is_staff', 'date_joined')
    
    # 4. Search capabilities
    search_fields = ('username', 'email', 'full_name', 'phone')

    # 5. Form editing layout structures (Only editing what belongs to the User model)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Profile Fields', {'fields': ('role', 'phone', 'full_name', 'dob')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Profile Fields', {'fields': ('role', 'phone', 'full_name', 'dob')}),
    )

    # Superusers/staff show as Admin regardless of the raw role field
    # (createsuperuser never touches role, so it sits at the 'patient' default).
    # Everyone else falls back to whatever role is actually set.
    @admin.display(description='Role', ordering='role')
    def assigned_role(self, obj):
        if obj.is_superuser or obj.is_staff:
            return 'Admin'
        return obj.get_role_display()

    # FIX: related_name on PatientProfile.user is 'patient_profile'
    # (with underscore) -- hasattr(obj, 'patientprofile') never matched.
    @admin.display(description='Gender')
    def patient_gender(self, obj):
        if hasattr(obj, 'patient_profile'):
            return obj.patient_profile.get_gender_display()
        return '-'

    @admin.display(description='Age')
    def patient_age(self, obj):
        if hasattr(obj, 'patient_profile'):
            return obj.patient_profile.age
        return '-'

# Register the model cleanly back into the system
admin.site.register(User, CustomUserAdmin)
