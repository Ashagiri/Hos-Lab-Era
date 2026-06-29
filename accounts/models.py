from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('technician', 'Lab Technician'),
        ('pathologist', 'Pathologist'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')  # Fixed here
    phone = models.CharField(max_length=15, blank=True, null=True)                    # Fixed here

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"