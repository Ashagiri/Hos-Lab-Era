from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect  # Handles immediate routing bounces

# Explicit views imports from your local application nodes
from laboratory.views import (
    home_view, 
    booking_view, 
    dashboard_view, 
    admin_dashboard_view, 
    download_report_view, 
    settings_view,
    record_test_result  
) 
from accounts.views import register_view, login_view

urlpatterns = [
    # 🔍 Bulletproof Shortcut: Bounces directly to the literal URL path string
    path('technician/', lambda request: redirect('/accounts/login/')),
   
    # 🛡️ Built-in Django Administrative Portal
    path('admin/', admin.site.urls),
    
    # 🏠 Public Marketing Welcome Homepage
    path('', home_view, name='home'),  
    
    # 👤 Dedicated Patient Dashboard Route
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # 💼 Dedicated Technician Command Center Dashboard
    path('dashboard/technician/', admin_dashboard_view, name='admin_dashboard'),
    
    # 📅 Patient Scheduling Operations
    path('booking/', booking_view, name='booking'),
    
    # ⚙️ Settings Profile Update Registry
    path('settings/', settings_view, name='settings'),
    
    # 🧪 Distributed Diagnostic Processing (The "Process" Button Action)
    path('dashboard/technician/process/<int:appointment_id>/', record_test_result, name='record_test_result'),
    
    # 📄 Automated Certified PDF Report Downloader 
    path('report/download/<int:appointment_id>/', download_report_view, name='download_report'),
    
    # 🔑 Authentication Management Ecosystem
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
]

# Serve Static Assets During Local Development Sharding
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)