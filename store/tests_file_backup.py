import json
from unittest.mock import patch

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from store.models import Payment, PaymentEvent


@pytest.mark.django_db
def test_start_checkout_creates_payment_and_redirects(client):
    # Préparer un produit et un tier
    from store.models import OfferTier, Product

    product = Product.objects.create(
        slug="test-prod", title="Test", price_fcfa=1000, is_published=True
    )
    tier = OfferTier.objects.create(
        product=product, kind="STANDARD", title="Standard", price_fcfa=1500
    )
    with patch("store.services.cinetpay.init_payment") as mock_init:
        mock_init.return_value = "https://pay.cinetpay.com/redirect"
        resp = client.post(
            reverse("store:start_checkout", args=[product.slug, tier.id]), {"email": "a@b.com"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "redirect_url" in data
        payment = Payment.objects.get(email="a@b.com")
        assert payment.amount == 1500
        assert payment.status == "PENDING"


@pytest.mark.django_db
def test_webhook_no_signature_returns_400(client):
    url = reverse("store:cinetpay_callback")
    resp = client.post(
        url, data=json.dumps({"transaction_id": "tx1"}), content_type="application/json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_webhook_bad_signature_returns_400(client, settings):
    url = reverse("store:cinetpay_callback")
    settings.CINETPAY_WEBHOOK_SECRET = "testsecret"
    payload = json.dumps({"transaction_id": "tx1"}).encode()
    bad_sig = "badtoken"
    resp = client.post(url, data=payload, content_type="application/json", HTTP_X_TOKEN=bad_sig)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_webhook_signature_ok_payment_check_ko(client, settings):
    from store.services import cinetpay

    url = reverse("store:cinetpay_callback")
    settings.CINETPAY_WEBHOOK_SECRET = "testsecret"
    # Créer un Payment
    payment = Payment.objects.create(
        order_id="tx2", amount=1000, currency="XOF", email="t@t.com", status="PENDING"
    )
    payload = json.dumps({"transaction_id": "tx2"}).encode()
    # Générer une signature valide
    import hashlib
    import hmac

    sig = hmac.new(settings.CINETPAY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    with patch.object(cinetpay, "payment_check", return_value=(False, None)):
        resp = client.post(url, data=payload, content_type="application/json", HTTP_X_TOKEN=sig)
        assert resp.status_code == 200
        payment.refresh_from_db()
        assert payment.status == "FAILED"
        assert PaymentEvent.objects.filter(payment=payment, kind="CHECK_FAIL").exists()


@pytest.mark.django_db
def test_webhook_signature_ok_payment_check_ok_and_delivery(client, settings):
    from store.services import cinetpay

    url = reverse("store:cinetpay_callback")
    settings.CINETPAY_WEBHOOK_SECRET = "testsecret"
    payment = Payment.objects.create(
        order_id="tx3", amount=1000, currency="XOF", email="t@t.com", status="PENDING"
    )
    payload = json.dumps({"transaction_id": "tx3"}).encode()
    import hashlib
    import hmac

    sig = hmac.new(settings.CINETPAY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    with patch.object(cinetpay, "payment_check", return_value=(True, "provider123")):
        with patch("store.views.deliver_ebook") as mock_deliver:
            resp = client.post(url, data=payload, content_type="application/json", HTTP_X_TOKEN=sig)
            assert resp.status_code == 200
            payment.refresh_from_db()
            assert payment.status == "PAID"
            assert payment.provider_tx_id == "provider123"
            assert PaymentEvent.objects.filter(payment=payment, kind="CHECK_OK").exists()
            mock_deliver.assert_called_once_with(payment)


@pytest.mark.django_db
def test_webhook_idempotent(client, settings):
    from store.services import cinetpay

    url = reverse("store:cinetpay_callback")
    settings.CINETPAY_WEBHOOK_SECRET = "testsecret"
    payment = Payment.objects.create(
        order_id="tx4", amount=1000, currency="XOF", email="t@t.com", status="PAID"
    )
    payload = json.dumps({"transaction_id": "tx4"}).encode()
    import hashlib
    import hmac

    sig = hmac.new(settings.CINETPAY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    with patch.object(cinetpay, "payment_check", return_value=(True, "provider123")):
        resp = client.post(url, data=payload, content_type="application/json", HTTP_X_TOKEN=sig)
        assert resp.status_code == 200
        payment.refresh_from_db()
        assert payment.status == "PAID"
        # Pas de double livraison
