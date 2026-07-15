from django.contrib import admin
from .models import PatientProfile, TestCategory, LabTest, Appointment


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'age', 'gender', 'registered_at')
    list_filter = ('gender', 'registered_at')
    search_fields = ('user__username', 'user__email', 'address')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(None)  # prevent cross-db JOIN

    def user_display(self, obj):
        return obj.user
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user'


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'category', 'price', 'normal_range', 'unit')
    list_filter = ('category',)
    search_fields = ('test_name', 'category__name')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # FIX: added appointment_date_only + appointment_time so the actual
    # selected slot is visible in the list view, instead of only showing
    # the DateTimeField's default midnight timestamp.
    list_display = ('id', 'patient_display', 'test', 'appointment_date_only', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('patient__username', 'test__test_name')
    list_select_related = ('test', 'test__category')  # only join within lab_db

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(None)

    def patient_display(self, obj):
        return obj.patient
    patient_display.short_description = 'Patient'
    patient_display.admin_order_field = 'patient'

    def appointment_date_only(self, obj):
        # Shows just the date (e.g. "July 15, 2026") without the
        # misleading ", midnight" suffix Django adds for DateTimeFields.
        return obj.appointment_date.date()
    appointment_date_only.short_description = 'Appointment Date'
    appointment_date_only.admin_order_field = 'appointment_date'
