from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Imports everything directly from your actual laboratory & accounts folders
from laboratory.views import (
    home_view, 
    booking_view, 
    dashboard_view, 
    download_report_view, 
    settings_view,
    record_test_result  # Added to support admin result entries
) 
from accounts.views import register_view, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Marketing welcome homepage (http://127.0.0.1:8000/)
    path('', home_view, name='home'),  
    
    # Booking panel route (http://127.0.0.1:8000/booking/)
    path('booking/', booking_view, name='booking'),
    
    # Dynamic Dashboard entry (http://127.0.0.1:8000/dashboard/)
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Admin Result Entry Operation Panel (http://127.0.0.1:8000/dashboard/record/.../)
    path('dashboard/record/<int:appointment_id>/', record_test_result, name='record_test_result'),
    
    # Automated PDF download compiler endpoint mapping rule
    path('dashboard/report/<int:appointment_id>/', download_report_view, name='download_report'),
    
    # Settings profile update route (http://127.0.0.1:8000/settings/)
    path('settings/', settings_view, name='settings'),
    
    # Authentication Management Views
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)