from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from laboratory.views import home_view, booking_view  # <-- We imported booking_view here
from accounts.views import register_view, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('booking/', booking_view, name='booking'),  # <-- We added this booking line!
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)