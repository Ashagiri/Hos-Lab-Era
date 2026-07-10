from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from laboratory.views import home_view, booking_view  # <-- We imported booking_view here
from accounts.views import register_view, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This empty path makes http://127.0.0.1:8000/ open the booking page instantly!
    path('', booking_view, name='home'),  
    
    path('booking/', booking_view, name='booking'),
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

