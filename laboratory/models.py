from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class PatientProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_profile'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"Patient Profile: {full_name}"


# =========================================================================
# AUTOMATIC PROFILE CREATION / SYNC SIGNALS
# =========================================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_patient_profile(sender, instance, created, **kwargs):
    """
    Ensures every User account automatically gets an associated PatientProfile,
    preventing MissingObject/DoesNotExist errors during template rendering.
    """
    if created:
        PatientProfile.objects.create(user=instance)
    else:
        # Save existing profile if present, or create missing profile for legacy users
        profile, _ = PatientProfile.objects.get_or_create(user=instance)
        profile.save()


# =========================================================================
# DIAGNOSTIC & CLINICAL ENTITIES
# =========================================================================

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
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
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
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_results'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Result for Appointment {self.appointment_id}"