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
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # Displays fields that exist exactly inside your models.py 
    list_display = ('id', 'patient', 'test', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('patient__username', 'test__test_name')