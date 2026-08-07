from django.db import models
from django.conf import settings

class PatientProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField(blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"

class TestCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class LabTest(models.Model):
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='tests')
    test_name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    normal_range = models.CharField(max_length=100, help_text="e.g., 70-100 mg/dL")
    unit = models.CharField(max_length=30, help_text="e.g., mg/dL, g/dL")

    def __str__(self):
        return f"{self.test_name} ({self.category.name})"
    
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT)
    appointment_date = models.DateTimeField()
    appointment_time = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} - {self.test.test_name} on {self.appointment_date.date()}"

class TestResult(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='result')
    result_value = models.CharField(max_length=100, help_text="The actual test outcome value recorded by admin")
    remarks = models.TextField(blank=True, null=True, help_text="Any diagnostic notes or remarks")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verified_results'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # FIXED INDENTATION HERE
    def __str__(self):
        return f"Result for Appointment {self.appointment_id}"