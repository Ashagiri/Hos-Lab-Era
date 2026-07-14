from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class CustomUserAdmin(BaseUserAdmin):
    # 1. Standard, clean column layout (safe for all template configurations)
    list_display = (
        'username', 
        'full_name', 
        'role',          # Shows the text role value cleanly
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

# Register the stable configuration
admin.site.register(User, CustomUserAdmin)