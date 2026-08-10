from django.db import migrations, models


def backfill_completed_at(apps, schema_editor):
    """
    Existing appointments that are already 'Completed' predate the new
    completed_at field, so it starts out empty for every one of them --
    which would make 'Today's Payment Collected' show Rs. 0 for all
    historical data. Backfill using the best real timestamp we have for
    when each one was actually finished: the linked TestResult's
    updated_at (set the moment a technician saved the result). If a
    Completed appointment has no TestResult at all (shouldn't normally
    happen, but just in case), fall back to its appointment_date so it
    isn't left blank.
    """
    Appointment = apps.get_model('laboratory', 'Appointment')
    for appt in Appointment.objects.filter(status='Completed', completed_at__isnull=True):
        result = getattr(appt, 'result', None)
        appt.completed_at = result.updated_at if result else appt.appointment_date
        appt.save(update_fields=['completed_at'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0007_appointment_doctor_id_appointment_doctor_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_completed_at, noop_reverse),
    ]
