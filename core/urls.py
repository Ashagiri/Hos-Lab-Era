from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Explicit views imports from your local application nodes
from laboratory.views import (
    home_view, 
    booking_view, 
    dashboard_view,
    technician_dashboard_view,
    download_report_view, 
    settings_view,
    record_test_result,
    check_slot_availability,
) 
from accounts.views import register_view, login_view, technician_login_view

urlpatterns = [
    # Dedicated Staff Portal Login View (Handles /technician/)
    path('technician/', technician_login_view, name='technician_login'),
   
    # Built-in Django Administrative Portal
    path('admin/', admin.site.urls),
    
    # Public Marketing Welcome Homepage
    path('', home_view, name='home'),  
    
    # Dedicated Patient Dashboard Route
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Dedicated Technician Command Center Dashboard 
    path('dashboard/technician/', technician_dashboard_view, name='technician_dashboard'),
    
    # Patient Scheduling Operations
    path('booking/', booking_view, name='booking'),
    path('booking/check-slots/', check_slot_availability, name='check_slot_availability'),
    
    # Settings Profile Update Registry
    path('settings/', settings_view, name='settings'),
    
    # Distributed Diagnostic Processing (The "Process" Button Action)
    path('dashboard/technician/process/<int:appointment_id>/', record_test_result, name='record_test_result'),
    
    # Automated Certified PDF Report Downloader 
    path('report/download/<int:appointment_id>/', download_report_view, name='download_report'),
    
    # Authentication Management Ecosystem
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
    
]

# Serve Static Assets During Local Development Sharding
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
