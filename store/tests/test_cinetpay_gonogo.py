import base64
import hashlib
import hmac
import json
import os
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from store.models import Payment

HEADER = os.getenv("CINETPAY_WEBHOOK_HEADER", "x-token")
SECRET = "testsecret"


def make_payload(
    order_id: str, amount: int = 15000, currency: str = "XOF", status: str = "PAID"
) -> dict:
    return {
        "transaction_id": order_id,
        "cpm_trans_id": order_id,
        "order_id": order_id,
        "status": status,
        "amount": amount,
        "currency": currency,
    }


def raw_json_bytes(body: dict) -> bytes:
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sig_hex(raw: bytes) -> str:
    return hmac.new(SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def sig_b64(raw: bytes) -> str:
    digest = hmac.new(SECRET.encode("utf-8"), raw, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def sig_hexpref(raw: bytes) -> str:
    return f"sha256={sig_hex(raw)}"


def hdr_key() -> str:
    return f"HTTP_{HEADER.upper().replace('-', '_')}"


class CinetpayGoNoGoTests(TestCase):
    def setUp(self):
        self.client = Client()
        os.environ["CINETPAY_WEBHOOK_SECRET"] = SECRET
        os.environ["CINETPAY_WEBHOOK_HEADER"] = HEADER

    def test_return_page_never_delivers(self):
        resp = self.client.get(reverse("store:payment_return"))
        self.assertEqual(resp.status_code, 200)

    def test_webhook_no_signature(self):
        p = Payment.objects.create(
            order_id="ORD-NOSIG", status="PENDING", amount=15000, currency="XOF"
        )
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        resp = self.client.post("/payment/callback/", data=raw, content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_webhook_invalid_signature(self):
        p = Payment.objects.create(
            order_id="ORD-BAD", status="PENDING", amount=15000, currency="XOF"
        )
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        resp = self.client.post(
            "/payment/callback/", data=raw, content_type="application/json", **{hdr_key(): "bad"}
        )
        self.assertEqual(resp.status_code, 400)

    @patch("store.views.payment_check", return_value=(False, None))
    @patch("store.views.deliver_ebook")
    def test_webhook_valid_signature_check_ko(self, mock_deliver, mock_check):
        p = Payment.objects.create(
            order_id="ORD-KO", status="PENDING", amount=15000, currency="XOF"
        )
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_hex(raw)
        resp = self.client.post(
            "/payment/callback/", data=raw, content_type="application/json", **{hdr_key(): sig}
        )
        self.assertEqual(resp.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.status, "FAILED")
        mock_deliver.assert_not_called()

    @patch("store.views.payment_check", return_value=(True, "PROVIDER123"))
    @patch("store.views.deliver_ebook")
    def test_webhook_valid_signature_check_ok(self, mock_deliver, mock_check):
        p = Payment.objects.create(
            order_id="ORD-OK", status="PENDING", amount=15000, currency="XOF"
        )
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_hex(raw)
        resp = self.client.post(
            "/payment/callback/", data=raw, content_type="application/json", **{hdr_key(): sig}
        )
        self.assertEqual(resp.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.status, "PAID")
        mock_deliver.assert_called_once()

    @patch("store.views.payment_check", return_value=(True, "PROVIDER123"))
    @patch("store.views.deliver_ebook")
    def test_webhook_idempotence(self, mock_deliver, mock_check):
        p = Payment.objects.create(
            order_id="ORD-IDEMPOT", status="PENDING", amount=15000, currency="XOF"
        )
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_hex(raw)
        # Premier appel : livraison
        resp1 = self.client.post(
            "/payment/callback/", data=raw, content_type="application/json", **{hdr_key(): sig}
        )
        self.assertEqual(resp1.status_code, 200)
        # Deuxième appel : pas de double livraison
        resp2 = self.client.post(
            "/payment/callback/", data=raw, content_type="application/json", **{hdr_key(): sig}
        )
        self.assertEqual(resp2.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.status, "PAID")
        mock_deliver.assert_called_once()
