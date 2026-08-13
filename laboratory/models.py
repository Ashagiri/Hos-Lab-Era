import uuid

from django.db import models
from django.conf import settings


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
    age = models.IntegerField(default=0, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M', blank=True, null=True)
    address = models.TextField(blank=True, null=True, default='')
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
    REFERRAL_CHOICES = (
        ('self', 'Self'),
        ('doctor', 'Doctor'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
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

    # Set the moment the appointment actually becomes 'Completed' (i.e. when
    # payment is effectively collected). This is intentionally separate from
    # appointment_date, which is only the originally SCHEDULED test date/time
    # and may be in the past or future relative to when the test was really
    # carried out and paid for.
    completed_at = models.DateTimeField(null=True, blank=True)

    # Referral details captured at booking time
    referral_type = models.CharField(max_length=10, choices=REFERRAL_CHOICES, default='self')
    doctor_name = models.CharField(max_length=150, blank=True, null=True)
    doctor_id = models.CharField(max_length=50, blank=True, null=True)

    # Snapshot of patient profile at time of booking (so later profile edits
    # don't retroactively change what a report says)
    patient_address = models.TextField(blank=True, null=True)
    patient_age = models.IntegerField(blank=True, null=True)
    patient_gender = models.CharField(max_length=1, blank=True, null=True)

    # Payment tracking. A booking can only be paid for once its Payment
    # (see below) is marked successful by the gateway callback / manual
    # bank-transfer verification -- this field is a cheap denormalized
    # flag so templates and staff views don't need to join into Payment
    # just to show a paid/unpaid pill.
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid'
    )

    def __str__(self):
        return f"{self.patient.username} - {self.test.test_name} on {self.appointment_date.date()}"


class Payment(models.Model):
    """
    One Payment record represents a single checkout -- it can cover
    several Appointments booked together in the same trip through the
    booking form (a patient may select multiple tests at once), all
    paid for with a single gateway transaction.
    """
    METHOD_CHOICES = (
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('fonepay', 'Fonepay'),
        ('nic_asia', 'NIC Asia Bank Transfer'),
        ('cash', 'Pay at Lab (Cash)'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    transaction_uuid = models.CharField(
        max_length=64, unique=True, default=uuid.uuid4, editable=False
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    appointments = models.ManyToManyField(Appointment, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Gateway reference captured on success/failure -- eSewa's `ref_id`,
    # Khalti's `pidx`/`transaction_id`, Fonepay's `bankTransactionId`, or
    # (for manual bank transfer) whatever deposit slip / reference number
    # the patient typed in for an admin to verify.
    gateway_ref = models.CharField(max_length=150, blank=True, null=True)
    raw_response = models.TextField(blank=True, null=True)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments',
        help_text="Set for manual methods (e.g. NIC Asia bank transfer) confirmed by staff.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        method_label = self.get_method_display() if self.method else 'No method selected'
        return f"Payment {self.transaction_uuid} - {method_label} - {self.get_status_display()}"

    def mark_success(self, gateway_ref=None, raw_response=None, verified_by=None):
        self.status = 'success'
        if gateway_ref is not None:
            self.gateway_ref = gateway_ref
        if raw_response is not None:
            self.raw_response = raw_response
        if verified_by is not None:
            self.verified_by = verified_by
        self.save()
        self.appointments.update(payment_status='paid')

    def mark_failed(self, raw_response=None):
        self.status = 'failed'
        if raw_response is not None:
            self.raw_response = raw_response
        self.save()
        self.appointments.update(payment_status='failed')


class TestResult(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='result')
    result_value = models.CharField(max_length=100, help_text="The actual test outcome value recorded by admin")
    remarks = models.TextField(blank=True, null=True, help_text="Any diagnostic notes or remarks")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
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
