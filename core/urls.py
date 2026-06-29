from django.contrib import admin
from django.urls import path
from laboratory.views import home_view
from accounts.views import register_view, login_view  # Import your new views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/register/', register_view, name='register'),  # Registration route
    path('accounts/login/', login_view, name='login'),          # Login route
]