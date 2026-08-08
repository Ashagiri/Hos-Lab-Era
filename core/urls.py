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
    admin_dashboard_view,
    admin_patient_records_view,
    admin_technician_records_view,
    download_report_view,
    settings_view,
    check_slot_availability,
    generate_report_view,
    reports_list,
    view_test_requests,
    patient_reports_view,
    booking_status_view,
    cancel_booking_view,
)
from accounts.views import register_view, login_view, technician_login_view, admin_login_view, logout_view

urlpatterns = [
    # Dedicated Staff Portal Login View (Handles /technician/)
    path('technician/', technician_login_view, name='technician_login'),

    # Dedicated Administrator Portal Login View (Handles /admin-portal/)
    # NOTE: kept separate from Django's own /admin/ path below.
    path('admin-portal/', admin_login_view, name='admin_login'),

    # Built-in Django Administrative Portal (advanced/raw data management --
    # linked to from within the professional Admin Dashboard for staff who
    # need it, but no longer the primary landing page for admin logins).
    path('admin/', admin.site.urls),

    # Public Marketing Welcome Homepage
    path('', home_view, name='home'),

    # Dedicated Patient Dashboard Route
    path('dashboard/', dashboard_view, name='dashboard'),

    # Dedicated Technician Command Center Dashboard
    path('dashboard/technician/', technician_dashboard_view, name='technician_dashboard'),

    # Dedicated standalone "View Test Requests" page
    path('dashboard/technician/requests/', view_test_requests, name='view_test_requests'),

    # Professional Admin Command Center Dashboard + records pages
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/admin/patients/', admin_patient_records_view, name='admin_patient_records'),
    path('dashboard/admin/technicians/', admin_technician_records_view, name='admin_technician_records'),

    # Patient Scheduling Operations
    path('booking/', booking_view, name='booking'),
    path('booking/check-slots/', check_slot_availability, name='check_slot_availability'),

    # Settings Profile Update Registry
    path('settings/', settings_view, name='settings'),

    # Dedicated Patient "My Reports" Page
    path('reports/', patient_reports_view, name='patient_reports'),

    # Dedicated Patient "Bookings Status" Live Tracker Page
    path('bookings/status/', booking_status_view, name='booking_status'),
    path('bookings/<int:appointment_id>/cancel/', cancel_booking_view, name='cancel_booking'),

    # Reports: list/picker page, then per-appointment generate view.
    # This single endpoint now handles both "Input Results" (from the
    # requests queue) and "Review & Sign" (from the reports queue) --
    # the old /process/<id>/ -> record_test_result endpoint is retired.
    path('dashboard/technician/reports/', reports_list, name='reports_list'),
    path('dashboard/technician/reports/<int:appointment_id>/', generate_report_view, name='generate_reports'),

    # Automated Certified PDF Report Downloader
    path('report/download/<int:appointment_id>/', download_report_view, name='download_report'),

    # Authentication Management Ecosystem
    path('accounts/register/', register_view, name='register'),
    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),
]

# Serve Static Assets During Local Development Sharding
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
