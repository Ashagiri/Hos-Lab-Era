from django.contrib import admin
from .models import PatientProfile, TestCategory, LabTest, Appointment, TestResult

# 💡 Inline Results allows technicians/admins to record medical outcomes right inside the Appointment pane!
class TestResultInline(admin.StackedInline):
    model = TestResult
    extra = 0
    fields = ('result_value', 'remarks', 'updated_by')
    readonly_fields = ('updated_at',)


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    # CORRECTED: Changed raw database fields to smart helper methods to prevent schema validation errors
    list_display = ('user', 'get_age', 'get_gender', 'registered_at')
    list_filter = ('registered_at',)
    search_fields = ('user__username', 'user__full_name', 'user__email', 'address')

    # Safe display for patient age fetched from custom user profiles
    @admin.display(description='Age')
    def get_age(self, obj):
        return getattr(obj.user, 'age', '-')

    # Safe display for patient gender fetched from custom user profiles
    @admin.display(description='Gender')
    def get_gender(self, obj):
        return getattr(obj.user, 'gender', '-')


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
    # Fully cross-compatible with your exact models.py structure
    list_display = ('patient', 'test', 'appointment_date', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'created_at')
    
    # Fully optimized lookup path to prevent any AttributeError breakdowns
    search_fields = ('patient__username', 'patient__full_name', 'test__test_name')
    ordering = ('-appointment_date',)
    
    inlines = [TestResultInline]

    # Auto-assigns the logged-in admin/tech user to the 'updated_by' slot on save
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TestResult):
                instance.updated_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'result_value', 'updated_by', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('appointment__patient__username', 'result_value', 'remarks')