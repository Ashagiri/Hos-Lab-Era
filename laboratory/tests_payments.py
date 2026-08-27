"""
Tests for laboratory/payments.py -- the HMAC signing and verification
helpers behind the eSewa and Fonepay checkout flows.

Why these tests exist: this file is the one place in the project where a
subtle bug (e.g. accidentally using `==` instead of `hmac.compare_digest`,
or verifying against the wrong fields) would let someone forge a "payment
succeeded" callback without actually paying. These tests exist to catch
that kind of regression before it ships, since there's currently no
coverage for it at all.

Run with:
    python manage.py test laboratory.tests_payments
"""
import base64
import hashlib
import hmac
import json
from types import SimpleNamespace

from django.test import TestCase, override_settings

from laboratory.payments import (
    esewa_signature,
    build_esewa_form_fields,
    verify_esewa_response,
    fonepay_signature,
    build_fonepay_form_fields,
    verify_fonepay_callback,
)


def make_payment(amount="500.00", transaction_uuid="txn-test-0001"):
    """A lightweight stand-in for a Payment model instance.

    build_esewa_form_fields / build_fonepay_form_fields only ever read
    `.amount` and `.transaction_uuid` off the object they're given, so a
    plain object with those two attributes is enough -- no database or
    migrations required to test the signing logic in isolation.
    """
    return SimpleNamespace(amount=float(amount), transaction_uuid=transaction_uuid)


@override_settings(
    ESEWA_PRODUCT_CODE="EPAYTEST",
    ESEWA_SECRET_KEY="8gBm/:&EnhH.1/q",
)
class EsewaSignatureTests(TestCase):

    def test_signature_is_deterministic(self):
        """Same inputs must always produce the same signature."""
        sig1 = esewa_signature("500.00", "txn-1", "EPAYTEST", "secret")
        sig2 = esewa_signature("500.00", "txn-1", "EPAYTEST", "secret")
        self.assertEqual(sig1, sig2)

    def test_signature_changes_if_amount_changes(self):
        """Changing any signed field must change the signature."""
        sig_a = esewa_signature("500.00", "txn-1", "EPAYTEST", "secret")
        sig_b = esewa_signature("999.00", "txn-1", "EPAYTEST", "secret")
        self.assertNotEqual(sig_a, sig_b)

    def test_build_form_fields_signature_matches_manual_computation(self):
        """The signature the form actually submits must match what you'd
        get by re-deriving it by hand from the same three fields."""
        payment = make_payment(amount="1200.00", transaction_uuid="txn-abc")
        fields = build_esewa_form_fields(payment, "https://x/success", "https://x/fail")

        message = (
            f"total_amount={fields['total_amount']},"
            f"transaction_uuid={fields['transaction_uuid']},"
            f"product_code={fields['product_code']}"
        )
        expected = base64.b64encode(
            hmac.new(b"8gBm/:&EnhH.1/q", message.encode(), hashlib.sha256).digest()
        ).decode()
        self.assertEqual(fields['signature'], expected)
        self.assertEqual(fields['total_amount'], "1200.00")
        self.assertEqual(fields['transaction_uuid'], "txn-abc")

    def _signed_success_payload(self, total_amount="500.00", transaction_uuid="txn-1", status="COMPLETE"):
        """Build a JSON payload the way eSewa's real success redirect
        would, correctly signed with our own secret key."""
        signed_field_names = "total_amount,transaction_uuid,product_code"
        message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code=EPAYTEST"
        signature = base64.b64encode(
            hmac.new(b"8gBm/:&EnhH.1/q", message.encode(), hashlib.sha256).digest()
        ).decode()
        payload = {
            "transaction_code": "abc123",
            "status": status,
            "total_amount": total_amount,
            "transaction_uuid": transaction_uuid,
            "product_code": "EPAYTEST",
            "signed_field_names": signed_field_names,
            "signature": signature,
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def test_verify_accepts_correctly_signed_payload(self):
        encoded = self._signed_success_payload()
        result = verify_esewa_response(encoded)
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "COMPLETE")

    def test_verify_rejects_tampered_amount(self):
        """Sign a payload for 500.00, then tamper the amount afterwards
        (as an attacker replaying/editing the redirect would). The
        signature no longer matches the modified field, so this must
        be rejected."""
        encoded = self._signed_success_payload(total_amount="500.00")
        payload = json.loads(base64.b64decode(encoded))
        payload["total_amount"] = "50000.00"  # attacker inflates the amount
        tampered_encoded = base64.b64encode(json.dumps(payload).encode()).decode()

        result = verify_esewa_response(tampered_encoded)
        self.assertIsNone(result)

    def test_verify_rejects_wrong_signature(self):
        payload = {
            "total_amount": "500.00",
            "transaction_uuid": "txn-1",
            "product_code": "EPAYTEST",
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": "not-a-real-signature==",
        }
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        self.assertIsNone(verify_esewa_response(encoded))

    def test_verify_rejects_garbage_input(self):
        """Non-base64 / non-JSON input must fail closed, not raise."""
        self.assertIsNone(verify_esewa_response("not-valid-base64-or-json"))
        self.assertIsNone(verify_esewa_response(""))

    def test_verify_rejects_missing_signed_field_names(self):
        payload = {"total_amount": "500.00"}  # no signed_field_names at all
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        self.assertIsNone(verify_esewa_response(encoded))


@override_settings(FONEPAY_MERCHANT_CODE="MERCH001", FONEPAY_SECRET_KEY="fonepay-secret")
class FonepaySignatureTests(TestCase):

    def test_signature_is_deterministic(self):
        fields = ["500.00", "prn-1", "MERCH001", "R1", "R2", "https://x/return"]
        sig1 = fonepay_signature(fields, "secret")
        sig2 = fonepay_signature(fields, "secret")
        self.assertEqual(sig1, sig2)

    def test_build_form_fields_dv_matches_manual_computation(self):
        payment = make_payment(amount="750.00", transaction_uuid="prn-xyz")
        fields = build_fonepay_form_fields(payment, "https://x/return")

        message = ",".join([
            fields['AMT'], fields['PRN'], "MERCH001",
            fields['R1'], fields['R2'], fields['RU'],
        ])
        expected_dv = hmac.new(b"fonepay-secret", message.encode(), hashlib.sha512).hexdigest()
        self.assertEqual(fields['DV'], expected_dv)

    def _signed_callback_params(self, amt="500.00", prn="prn-1", bid="bank-ref-1"):
        fields = [prn, "MERCH001", amt, "NPR", "uid-1", bid]
        dv = hmac.new(b"fonepay-secret", ",".join(fields).encode(), hashlib.sha512).hexdigest()
        return {
            "PRN": prn, "PID": "MERCH001", "AMT": amt, "CRN": "NPR",
            "UID": "uid-1", "BID": bid, "DV": dv,
        }

    def test_verify_accepts_correctly_signed_callback(self):
        params = self._signed_callback_params()
        self.assertTrue(verify_fonepay_callback(params))

    def test_verify_rejects_tampered_amount(self):
        """Same idea as the eSewa test: sign for one amount, then edit
        the amount an attacker would want to change post-signing."""
        params = self._signed_callback_params(amt="500.00")
        params["AMT"] = "999999.00"
        self.assertFalse(verify_fonepay_callback(params))

    def test_verify_rejects_wrong_dv(self):
        params = self._signed_callback_params()
        params["DV"] = "0" * 128
        self.assertFalse(verify_fonepay_callback(params))

    def test_verify_rejects_missing_fields_without_raising(self):
        """A malformed/incomplete callback must return False, not throw
        an uncaught exception that could 500 the endpoint."""
        self.assertFalse(verify_fonepay_callback({}))
