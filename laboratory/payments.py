"""
Payment gateway helpers for LabPortal.

Keeps all eSewa / Khalti / Fonepay wire-protocol details (signature
generation, request payloads, response verification) in one place, away
from the Django views, so the views only deal with our own Payment model.

Supported methods:
- eSewa   (ePay v2, HMAC-SHA256 signed form-POST redirect)
- Khalti  (ePayment v2, server-to-server initiate + lookup)
- Fonepay (HMAC-SHA512 signed redirect + verification)
- NIC Asia Bank (manual bank transfer, verified by staff -- no API)
"""
import base64
import hashlib
import hmac
import json

import requests
from django.conf import settings


# =========================================================================
# eSewa (ePay v2)
# =========================================================================

def esewa_signature(total_amount, transaction_uuid, product_code, secret_key):
    """
    HMAC-SHA256 signature over 'total_amount=...,transaction_uuid=...,product_code=...'
    Base64-encoded, exactly as required by eSewa's ePay v2 spec.
    """
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    digest = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(digest).decode('utf-8')


def build_esewa_form_fields(payment, success_url, failure_url):
    """
    Returns the dict of hidden <input> fields the browser must POST to
    ESEWA_PAYMENT_URL to start a checkout. eSewa itself expects the
    request to arrive as a real HTML form submission (not fetch/AJAX),
    so the view renders this into an auto-submitting form template.
    """
    total_amount = f"{payment.amount:.2f}"
    signed_field_names = "total_amount,transaction_uuid,product_code"
    signature = esewa_signature(
        total_amount, payment.transaction_uuid, settings.ESEWA_PRODUCT_CODE, settings.ESEWA_SECRET_KEY
    )
    return {
        'amount': total_amount,
        'tax_amount': "0",
        'total_amount': total_amount,
        'transaction_uuid': payment.transaction_uuid,
        'product_code': settings.ESEWA_PRODUCT_CODE,
        'product_service_charge': "0",
        'product_delivery_charge': "0",
        'success_url': success_url,
        'failure_url': failure_url,
        'signed_field_names': signed_field_names,
        'signature': signature,
    }


def verify_esewa_response(encoded_data):
    """
    Decodes the base64 `data` query param eSewa appends to success_url,
    then re-derives the signature and compares it (timing-safe) against
    the one eSewa sent, using ONLY the fields listed in signed_field_names
    -- never trust the payload without this check.
    Returns the decoded dict on success, or None if tampered/invalid.
    """
    try:
        decoded = base64.b64decode(encoded_data).decode('utf-8')
        payload = json.loads(decoded)
    except Exception:
        return None

    signed_field_names = payload.get('signed_field_names', '')
    fields = signed_field_names.split(',') if signed_field_names else []
    if not fields:
        return None

    message = ",".join(f"{field}={payload.get(field, '')}" for field in fields)
    digest = hmac.new(
        settings.ESEWA_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(digest).decode('utf-8')

    if not hmac.compare_digest(expected_signature, payload.get('signature', '')):
        return None

    return payload


def esewa_check_status(transaction_uuid, total_amount):
    """
    Defence-in-depth server-to-server confirmation, per eSewa's docs --
    the signature check above proves the browser wasn't tampered with,
    this proves eSewa's own servers actually recorded the transaction.
    """
    try:
        response = requests.get(
            settings.ESEWA_STATUS_CHECK_URL,
            params={
                'product_code': settings.ESEWA_PRODUCT_CODE,
                'total_amount': f"{total_amount:.2f}",
                'transaction_uuid': transaction_uuid,
            },
            timeout=10,
        )
        return response.json()
    except Exception:
        return None


# =========================================================================
# Khalti (ePayment v2)
# =========================================================================

def khalti_initiate(payment, return_url, website_url, patient):
    """
    Server-to-server call telling Khalti about the order; Khalti replies
    with a `pidx` (payment session id) and a `payment_url` we redirect
    the patient's browser to.
    """
    payload = {
        "return_url": return_url,
        "website_url": website_url,
        "amount": int(payment.amount * 100),  # Khalti wants paisa, not rupees
        "purchase_order_id": payment.transaction_uuid,
        "purchase_order_name": "LabPortal Diagnostic Test Booking",
        "customer_info": {
            "name": (patient.full_name or patient.get_full_name() or patient.username),
            "email": patient.email or "patient@example.com",
            "phone": patient.phone or "9800000000",
        },
    }
    try:
        response = requests.post(
            settings.KHALTI_INITIATE_URL,
            headers={
                'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        data = response.json()
        if response.status_code == 200 and 'payment_url' in data:
            return data, None
        return None, data
    except Exception as exc:
        return None, {'error': str(exc)}


def khalti_lookup(pidx):
    """Confirms the real status of a pidx directly with Khalti's servers."""
    try:
        response = requests.post(
            settings.KHALTI_LOOKUP_URL,
            headers={
                'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
                'Content-Type': 'application/json',
            },
            json={'pidx': pidx},
            timeout=15,
        )
        return response.json()
    except Exception as exc:
        return {'error': str(exc)}


# =========================================================================
# Fonepay
# =========================================================================

def fonepay_signature(fields, secret_key):
    """
    Fonepay signs a '/'-joined ordered list of field values with
    HMAC-SHA512, returned as a lowercase hex digest ("DV" / data
    verification field).
    """
    message = ",".join(fields)
    return hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha512).hexdigest()


def build_fonepay_form_fields(payment, return_url):
    amount = f"{payment.amount:.2f}"
    prn = payment.transaction_uuid  # Product Reference Number -- our unique order id
    remarks1 = "LabPortal"
    remarks2 = "Diagnostics"
    # Order fixed by Fonepay's spec: AMT,PRN,MD (merchant code),
    # remarks1, remarks2, then the return URL.
    fields = [amount, prn, settings.FONEPAY_MERCHANT_CODE, remarks1, remarks2, return_url]
    dv = fonepay_signature(fields, settings.FONEPAY_SECRET_KEY)
    return {
        'PID': settings.FONEPAY_MERCHANT_CODE,
        'MD': 'P',
        'AMT': amount,
        'CRN': 'NPR',
        'DT': '',
        'R1': remarks1,
        'R2': remarks2,
        'PRN': prn,
        'RU': return_url,
        'DV': dv,
    }


def verify_fonepay_callback(params):
    """
    Fonepay's return_url is called with PRN, PID, AMT, and their own DV
    (verification hash) among other fields. Recompute and compare.
    """
    try:
        fields = [
            params.get('PRN', ''),
            params.get('PID', ''),
            params.get('AMT', ''),
            params.get('CRN', 'NPR'),
            params.get('UID', ''),
            params.get('BID', ''),
        ]
        expected = hmac.new(
            settings.FONEPAY_SECRET_KEY.encode('utf-8'),
            ",".join(fields).encode('utf-8'),
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(expected, params.get('DV', ''))
    except Exception:
        return False
