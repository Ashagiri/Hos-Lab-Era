"""
laboratory.views is now a package split by user role, instead of one
1400-line file. Everything is re-exported here so existing imports like
    from laboratory.views import home_view, booking_view
keep working unchanged -- urls.py needed NO changes for this refactor.
"""

from .patient import (
    home_view,
    dashboard_view,
    booking_view,
    patient_reports_view,
    booking_status_view,
    cancel_booking_view,
    check_slot_availability,
    settings_view,
    download_report_view,
)
from .staff import (
    technician_dashboard_view,
    view_test_requests,
    generate_report_view,
    reports_list,
)
from .admin import (
    admin_dashboard_view,
    admin_patient_records_view,
    admin_technician_records_view,
    admin_add_technician_view,
    admin_edit_technician_view,
    admin_reports_list,
)

__all__ = [
    'home_view', 'dashboard_view', 'booking_view', 'patient_reports_view',
    'booking_status_view', 'cancel_booking_view', 'check_slot_availability',
    'settings_view', 'download_report_view',
    'technician_dashboard_view', 'view_test_requests', 'generate_report_view',
    'reports_list',
    'admin_dashboard_view', 'admin_patient_records_view',
    'admin_technician_records_view', 'admin_add_technician_view',
    'admin_edit_technician_view', 'admin_reports_list',
]
