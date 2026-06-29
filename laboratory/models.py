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
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)  # Fixed here
    address = models.TextField(blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"

class TestCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Fixed here
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class LabTest(models.Model):
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='tests')
    test_name = models.CharField(max_length=150)  # Fixed here
    price = models.DecimalField(max_digits=10, decimal_places=2)
    normal_range = models.CharField(max_length=100, help_text="e.g., 70-100 mg/dL")  # Fixed here
    unit = models.CharField(max_length=30, help_text="e.g., mg/dL, g/dL")  # Fixed here

    def __str__(self):
        return f"{self.test_name} ({self.category.name})"