from django.contrib import admin
from .models import PatientProfile, TestCategory, LabTest, Appointment, Payment


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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_uuid', 'patient_display', 'amount', 'method', 'status', 'gateway_ref', 'created_at')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('transaction_uuid', 'patient__username', 'patient__email', 'gateway_ref')
    readonly_fields = ('transaction_uuid', 'created_at', 'updated_at', 'raw_response')
    actions = ['approve_selected_payments', 'reject_selected_payments']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(None)

    def patient_display(self, obj):
        return obj.patient
    patient_display.short_description = 'Patient'
    patient_display.admin_order_field = 'patient'

    @admin.action(description="Approve selected payments (mark as Paid)")
    def approve_selected_payments(self, request, queryset):
        for payment in queryset:
            payment.mark_success(verified_by=request.user)
        self.message_user(request, f"{queryset.count()} payment(s) marked as paid.")

    @admin.action(description="Reject selected payments (mark as Failed)")
    def reject_selected_payments(self, request, queryset):
        for payment in queryset:
            payment.mark_failed()
        self.message_user(request, f"{queryset.count()} payment(s) marked as failed.")
