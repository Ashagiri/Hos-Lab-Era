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
        'patient_gender',  # Use the safe relative property method below
        'patient_age',     # Use the safe relative property method below
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

    # 💡 Safe Role Evaluator
    @admin.display(description='Role', ordering='role')
    def assigned_role(self, obj):
        if obj.is_superuser or obj.is_staff or str(obj.role).lower() == 'admin':
            return 'Admin'
        elif str(obj.role).lower() == 'tech' or 'tech' in obj.username.lower():
            return 'Technician'
        return '-'

    # 💡 Safe Patient Data Cross-Reference Accessors
    @admin.display(description='Gender')
    def patient_gender(self, obj):
        # Checks if a patient profile linked to this user exists safely across apps
        if hasattr(obj, 'patientprofile'):
            return obj.patientprofile.gender
        return '-'

    @admin.display(description='Age')
    def patient_age(self, obj):
        if hasattr(obj, 'patientprofile'):
            return obj.patientprofile.age
        return '-'

# Register the model cleanly back into the system
admin.site.register(User, CustomUserAdmin)