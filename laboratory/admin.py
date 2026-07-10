from django.contrib import admin
from .models import PatientProfile, TestCategory, LabTest

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'registered_at')
    list_filter = ('gender', 'registered_at')
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