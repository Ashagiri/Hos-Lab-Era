from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from laboratory.views import dashboard_view, home_view, booking_view  # Keeps both views active
from accounts.views import register_view, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # RESTORED: This puts your original welcome home page back at http://127.0.0.1:8000/
    path('', home_view, name='home'),  
    
    # This keeps your booking page over at http://127.0.0.1:8000/booking/
    path('booking/', booking_view, name='booking'),
    
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
    
    path('dashboard/', dashboard_view, name='dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)