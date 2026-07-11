from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

# UPDATED: Added settings_view alongside your other laboratory imports
from laboratory.views import home_view, booking_view, dashboard_view, download_report_view, settings_view 
from accounts.views import register_view, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Restores your original marketing welcome page back at http://127.0.0.1:8000/
    path('', home_view, name='home'),  
    
    # Booking engine panel route over at http://127.0.0.1:8000/booking/
    path('booking/', booking_view, name='booking'),
    
    # User data summary profile panel at http://127.0.0.1:8000/dashboard/
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # NEW: Automated PDF download compiler endpoint mapping rule
    path('dashboard/report/<int:appointment_id>/', download_report_view, name='download_report'),
    
    # NEW: Settings profile update route at http://127.0.0.1:8000/settings/
    path('settings/', settings_view, name='settings'),
    
    # Authentication Management Views
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
    path('laboratory/', include('laboratory.urls', namespace='laboratory')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)