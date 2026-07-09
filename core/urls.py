from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from laboratory.views import home_view
from accounts.views import register_view, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/register/', register_view, name='register'),  # Registration route
    path('accounts/login/', login_view, name='login'),            # Login route
]

# This configuration safely routes and delivers your static image files during local development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)