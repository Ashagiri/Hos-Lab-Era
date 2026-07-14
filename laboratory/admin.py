from django.contrib import admin
from .models import PatientProfile, TestCategory, LabTest, Appointment

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    # Aligns perfectly with your database fields
    list_display = ('user', 'age', 'gender', 'registered_at')
    list_filter = ('gender', 'registered_at')
    # Traverses through the OneToOneField relationship to query the User model attributes safely
    search_fields = ('user__username', 'user__email', 'address')


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'category', 'price', 'normal_range', 'unit')
    list_filter = ('category',)
    search_fields = ('test_name', 'category__name')

try:
    admin.site.unregister(Appointment)
except admin.sites.NotRegistered:
    pass

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # These create the actual table column headers
    list_display = [
        'patient', 
        'get_patient_age', 
        'get_patient_gender', 
        'test', 
        'appointment_date', 
        'status'
    ]
    
    list_filter = ('status', 'appointment_date')
    search_fields = ('patient__username', 'patient__email', 'test__test_name')

    # Custom column data methods
    def get_patient_age(self, obj):
        profile = PatientProfile.objects.filter(user=obj.patient).first()
        return profile.age if profile else "—"
    get_patient_age.short_description = 'Age'  # Sets the header text

    def get_patient_gender(self, obj):
        profile = PatientProfile.objects.filter(user=obj.patient).first()
        return profile.gender if profile else "—"
    get_patient_gender.short_description = 'Gender'