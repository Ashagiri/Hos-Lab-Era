import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Payment
from . import payments as gateway
from accounts.decorators import is_lab_staff

logger = logging.getLogger(__name__)


def _absolute_url(request, name, *args):
    return request.build_absolute_uri(reverse(name, args=args))


@login_required
def payment_select_view(request, transaction_uuid):
    """
    Lets the patient pick how they want to pay for the booking they just
    made (eSewa / Khalti / Fonepay / NIC Asia bank transfer / cash at the
    lab), then hands off to the right gateway flow.
    """
    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid, patient=request.user)

    if payment.status == 'success':
        messages.info(request, "This booking has already been paid for.")
        return redirect('booking_status')

    if request.method == 'POST':
        method = request.POST.get('method')
        valid_methods = dict(Payment.METHOD_CHOICES)
        if method not in valid_methods:
            messages.error(request, "Please choose a valid payment method.")
            return redirect('payment_select', transaction_uuid=transaction_uuid)

        payment.method = method
        payment.status = 'processing' if method != 'cash' else 'pending'
        payment.save()

        if method == 'esewa':
            return redirect('payment_esewa_pay', transaction_uuid=transaction_uuid)
        elif method == 'khalti':
            return redirect('payment_khalti_pay', transaction_uuid=transaction_uuid)
        elif method == 'fonepay':
            return redirect('payment_fonepay_pay', transaction_uuid=transaction_uuid)
        elif method == 'nic_asia':
            return redirect('payment_bank_transfer', transaction_uuid=transaction_uuid)
        elif method == 'cash':
            messages.success(
                request,
                "Your booking is confirmed. Please pay the amount in cash "
                "at the lab reception during your appointment."
            )
            return redirect('booking_status')

    return render(request, 'laboratory/payment_select.html', {
        'payment': payment,
        'appointments': payment.appointments.select_related('test'),
    })


@login_required
def payment_esewa_pay(request, transaction_uuid):
    """Renders the auto-submitting hidden form that hands the browser to eSewa."""
    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid, patient=request.user, method='esewa')

    success_url = _absolute_url(request, 'payment_esewa_success')
    failure_url = _absolute_url(request, 'payment_esewa_failure') + f"?transaction_uuid={payment.transaction_uuid}"

    fields = gateway.build_esewa_form_fields(payment, success_url, failure_url)

    return render(request, 'laboratory/payment_gateway_redirect.html', {
        'action_url': settings.ESEWA_PAYMENT_URL,
        'fields': fields,
        'gateway_name': 'eSewa',
    })


@login_required
def payment_esewa_success(request):
    """eSewa's success_url callback -- verifies signature then double-checks with eSewa's status API."""
    encoded_data = request.GET.get('data')
    payload = gateway.verify_esewa_response(encoded_data) if encoded_data else None

    if not payload:
        messages.error(request, "We couldn't verify the eSewa response. If money was deducted, contact support.")
        return redirect('booking_status')

    transaction_uuid = payload.get('transaction_uuid')
    payment = Payment.objects.filter(transaction_uuid=transaction_uuid, patient=request.user).first()
    if not payment:
        messages.error(request, "Payment record not found for this transaction.")
        return redirect('booking_status')

    status_result = gateway.esewa_check_status(transaction_uuid, payment.amount)
    if status_result and status_result.get('status') == 'COMPLETE':
        payment.mark_success(
            gateway_ref=payload.get('transaction_code') or status_result.get('ref_id'),
            raw_response=str(status_result),
        )
        messages.success(request, "Payment received via eSewa. Your booking is confirmed!")
    else:
        payment.mark_failed(raw_response=str(status_result))
        messages.error(request, "eSewa could not confirm this payment. Please try again.")

    return redirect('payment_result', transaction_uuid=payment.transaction_uuid)


@login_required
def payment_esewa_failure(request):
    transaction_uuid = request.GET.get('transaction_uuid')
    payment = Payment.objects.filter(transaction_uuid=transaction_uuid, patient=request.user).first()
    if payment:
        payment.mark_failed(raw_response="User cancelled or eSewa reported failure.")
        messages.error(request, "Your eSewa payment was not completed.")
        return redirect('payment_result', transaction_uuid=payment.transaction_uuid)
    messages.error(request, "Your eSewa payment was not completed.")
    return redirect('booking_status')


@login_required
def payment_khalti_pay(request, transaction_uuid):
    """Server-to-server initiate call, then redirect the browser to Khalti's payment_url."""
    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid, patient=request.user, method='khalti')

    if not settings.KHALTI_SECRET_KEY:
        messages.error(
            request,
            "Khalti isn't configured yet -- add KHALTI_SECRET_KEY to the .env file "
            "(get a free test key from test-admin.khalti.com). Please choose another method for now."
        )
        return redirect('payment_select', transaction_uuid=transaction_uuid)

    return_url = _absolute_url(request, 'payment_khalti_return')
    website_url = request.build_absolute_uri('/')

    data, error = gateway.khalti_initiate(payment, return_url, website_url, request.user)
    if not data:
        logger.warning("Khalti initiate failed for %s: %s", transaction_uuid, error)
        payment.mark_failed(raw_response=str(error))
        messages.error(request, "Could not start the Khalti checkout. Please try another payment method.")
        return redirect('payment_select', transaction_uuid=transaction_uuid)

    payment.gateway_ref = data.get('pidx')
    payment.save()
    return redirect(data['payment_url'])


@login_required
def payment_khalti_return(request):
    """Khalti's return_url -- always re-verify server-side via /lookup/, never trust the query string alone."""
    pidx = request.GET.get('pidx')
    payment = Payment.objects.filter(gateway_ref=pidx, patient=request.user, method='khalti').first()
    if not payment:
        messages.error(request, "Payment record not found for this Khalti transaction.")
        return redirect('booking_status')

    result = gateway.khalti_lookup(pidx)
    if result.get('status') == 'Completed':
        payment.mark_success(gateway_ref=result.get('transaction_id', pidx), raw_response=str(result))
        messages.success(request, "Payment received via Khalti. Your booking is confirmed!")
    else:
        payment.mark_failed(raw_response=str(result))
        messages.error(request, f"Khalti payment status: {result.get('status', 'Unknown')}.")

    return redirect('payment_result', transaction_uuid=payment.transaction_uuid)


@login_required
def payment_fonepay_pay(request, transaction_uuid):
    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid, patient=request.user, method='fonepay')

    if not settings.FONEPAY_MERCHANT_CODE or not settings.FONEPAY_SECRET_KEY:
        messages.error(
            request,
            "Fonepay isn't configured yet -- add FONEPAY_MERCHANT_CODE and FONEPAY_SECRET_KEY "
            "to the .env file once Fonepay issues your merchant credentials. Please choose another method for now."
        )
        return redirect('payment_select', transaction_uuid=transaction_uuid)

    return_url = _absolute_url(request, 'payment_fonepay_return')
    fields = gateway.build_fonepay_form_fields(payment, return_url)

    return render(request, 'laboratory/payment_gateway_redirect.html', {
        'action_url': settings.FONEPAY_PAYMENT_URL,
        'fields': fields,
        'gateway_name': 'Fonepay',
    })


@login_required
def payment_fonepay_return(request):
    params = request.GET.dict()
    prn = params.get('PRN')
    payment = Payment.objects.filter(transaction_uuid=prn, patient=request.user, method='fonepay').first()
    if not payment:
        messages.error(request, "Payment record not found for this Fonepay transaction.")
        return redirect('booking_status')

    if gateway.verify_fonepay_callback(params) and params.get('PS', '').lower() in ('true', 'success', 'completed'):
        payment.mark_success(gateway_ref=params.get('BID') or params.get('UID'), raw_response=str(params))
        messages.success(request, "Payment received via Fonepay. Your booking is confirmed!")
    else:
        payment.mark_failed(raw_response=str(params))
        messages.error(request, "Fonepay could not confirm this payment. Please try again.")

    return redirect('payment_result', transaction_uuid=payment.transaction_uuid)


@login_required
def payment_bank_transfer_view(request, transaction_uuid):
    """
    NIC Asia (and any other bank) direct-deposit flow: show account
    details, let the patient record the reference number from their
    deposit slip / mobile banking receipt, then wait for staff to
    confirm it against the bank statement.
    """
    payment = get_object_or_404(
        Payment, transaction_uuid=transaction_uuid, patient=request.user, method='nic_asia'
    )

    if request.method == 'POST':
        reference = request.POST.get('reference_number', '').strip()
        if not reference:
            messages.error(request, "Please enter the transaction/reference number from your deposit or transfer.")
            return redirect('payment_bank_transfer', transaction_uuid=transaction_uuid)

        payment.gateway_ref = reference
        payment.status = 'processing'
        payment.save()
        messages.success(
            request,
            "Thanks! We've recorded your NIC Asia Bank transfer reference. "
            "Our staff will verify it against the bank statement and confirm your booking shortly."
        )
        return redirect('booking_status')

    return render(request, 'laboratory/payment_bank_transfer.html', {
        'payment': payment,
        'bank_name': "NIC Asia Bank",
        'account_name': settings.NIC_ASIA_ACCOUNT_NAME,
        'account_number': settings.NIC_ASIA_ACCOUNT_NUMBER,
        'branch': settings.NIC_ASIA_BRANCH,
    })


@login_required
def payment_result_view(request, transaction_uuid):
    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid, patient=request.user)
    return render(request, 'laboratory/payment_result.html', {'payment': payment})


# =========================================================================
# STAFF: Verify manual (bank transfer) payments
# =========================================================================

@login_required
def admin_payments_view(request):
    """
    Lists every payment so admins can see gateway payments at a glance
    and manually confirm/reject bank-transfer (NIC Asia) payments that
    are waiting on a human to check the bank statement.
    """
    if not is_lab_staff(request.user):
        messages.error(request, "Access restricted to authorized management profiles.")
        return redirect('dashboard')

    method_filter = request.GET.get('method', '').strip()
    status_filter = request.GET.get('status', '').strip()

    payment_qs = Payment.objects.select_related('patient').prefetch_related('appointments__test').order_by('-created_at')
    if method_filter:
        payment_qs = payment_qs.filter(method=method_filter)
    if status_filter:
        payment_qs = payment_qs.filter(status=status_filter)

    return render(request, 'laboratory/admin_payments.html', {
        'payments': payment_qs,
        'method_filter': method_filter,
        'status_filter': status_filter,
        'method_choices': Payment.METHOD_CHOICES,
        'status_choices': Payment.STATUS_CHOICES,
    })


@login_required
def admin_verify_payment_view(request, payment_id):
    if not is_lab_staff(request.user):
        messages.error(request, "Access restricted to authorized management profiles.")
        return redirect('dashboard')

    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            payment.mark_success(verified_by=request.user)
            messages.success(request, f"Payment {payment.transaction_uuid} confirmed as paid.")
        elif action == 'reject':
            payment.mark_failed()
            messages.warning(request, f"Payment {payment.transaction_uuid} marked as failed.")

    return redirect('admin_payments')
