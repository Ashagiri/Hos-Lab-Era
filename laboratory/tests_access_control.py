"""
Cross-role access control tests.

These exist specifically because of a real bug found in review:
`reports_list` (dashboard/technician/reports/) had `@login_required`
but NO role check, so any authenticated patient could browse every
other patient's completed appointment (name, test, date) just by
visiting the technician URL directly.

The fix moved every staff/admin view onto one shared decorator
(accounts.decorators.role_required) instead of N hand-copied inline
checks. These tests assert the *behaviour* -- a patient account really
is blocked from every staff/admin page -- so a future edit that removes
the decorator from one view again will fail CI, not just look wrong on
code review.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Appointment, LabTest, TestCategory

User = get_user_model()


class RoleGatedViewsTests(TestCase):
    """Every staff/admin URL must reject a plain patient account."""

    @classmethod
    def setUpTestData(cls):
        cls.patient = User.objects.create_user(
            username="patient1", password="pw-Str0ngpass!", role="patient"
        )
        cls.technician = User.objects.create_user(
            username="tech1", password="pw-Str0ngpass!", role="technician"
        )
        cls.admin = User.objects.create_user(
            username="admin1", password="pw-Str0ngpass!", role="admin"
        )

        category = TestCategory.objects.create(name="Hematology")
        test = LabTest.objects.create(
            category=category, test_name="CBC", price=500,
            normal_range="4-11", unit="x10^3/uL",
        )
        cls.other_patient = User.objects.create_user(
            username="patient2", password="pw-Str0ngpass!", role="patient"
        )
        cls.appointment = Appointment.objects.create(
            patient=cls.other_patient, test=test,
            appointment_date="2026-01-01", status="Completed",
        )

    # ---- the specific regression: reports_list must now be gated ----

    def test_patient_cannot_browse_technician_reports_list(self):
        """
        Regression test for the IDOR: a patient must NOT be able to see
        the full cross-patient reports list by hitting the technician
        URL directly.
        """
        self.client.login(username="patient1", password="pw-Str0ngpass!")
        response = self.client.get(reverse("reports_list"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_technician_can_view_reports_list(self):
        self.client.login(username="tech1", password="pw-Str0ngpass!")
        response = self.client.get(reverse("reports_list"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_reports_list(self):
        self.client.login(username="admin1", password="pw-Str0ngpass!")
        response = self.client.get(reverse("reports_list"))
        self.assertEqual(response.status_code, 200)

    # ---- sweep: every staff/admin page rejects a patient ----

    def test_patient_is_blocked_from_every_staff_and_admin_page(self):
        self.client.login(username="patient1", password="pw-Str0ngpass!")

        staff_urls_redirect_to_login = [
            reverse("technician_dashboard"),
        ]
        for url in staff_urls_redirect_to_login:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, reverse("login"))

        staff_urls_redirect_to_dashboard = [
            reverse("view_test_requests"),
            reverse("reports_list"),
            reverse("generate_reports", args=[self.appointment.id]),
        ]
        for url in staff_urls_redirect_to_dashboard:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, reverse("dashboard"))

        admin_urls_redirect_to_login = [
            reverse("admin_dashboard"),
            reverse("admin_patient_records"),
            reverse("admin_technician_records"),
            reverse("admin_add_technician"),
            reverse("admin_reports_list"),
        ]
        for url in admin_urls_redirect_to_login:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, reverse("login"))

    def test_technician_is_blocked_from_admin_only_pages(self):
        """A technician account must not be treated as an admin."""
        self.client.login(username="tech1", password="pw-Str0ngpass!")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertRedirects(response, reverse("login"))

    def test_anonymous_user_is_redirected_to_login_everywhere(self):
        for url in [
            reverse("reports_list"),
            reverse("technician_dashboard"),
            reverse("admin_dashboard"),
        ]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    # ---- object-level access control on reports/downloads ----

    def test_patient_cannot_download_another_patients_report(self):
        self.client.login(username="patient1", password="pw-Str0ngpass!")
        response = self.client.get(
            reverse("download_report", args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_owning_patient_can_download_their_own_report(self):
        self.client.login(username="patient2", password="pw-Str0ngpass!")
        response = self.client.get(
            reverse("download_report", args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_staff_can_download_any_patients_report(self):
        self.client.login(username="tech1", password="pw-Str0ngpass!")
        response = self.client.get(
            reverse("download_report", args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 200)
