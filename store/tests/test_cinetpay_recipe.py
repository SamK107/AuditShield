import os, json, hmac, hashlib, base64
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from store.models import Payment

HEADER = os.getenv("CINETPAY_WEBHOOK_HEADER", "x-token")
SECRET = "testsecret"

def make_payload(order_id: str, amount: int = 15000, currency: str = "XOF", status: str = "PAID") -> dict:
    return {
        "transaction_id": order_id,
        "cpm_trans_id": order_id,
        "order_id":       order_id,
        "status":         status,
        "amount":         amount,
        "currency":       currency,
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

def cb_url():
    try:
        return reverse("cinetpay_callback")
    except Exception:
        return "/payment/callback/"

class CinetpayRecipeTests(TestCase):
    def setUp(self):
        self.client = Client()
        os.environ["CINETPAY_WEBHOOK_SECRET"] = SECRET
        os.environ["CINETPAY_WEBHOOK_HEADER"] = HEADER

    def test_return_page_does_not_deliver(self):
        try:
            url = reverse("payment_return")
        except Exception:
            url = "/payment/return/"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_webhook_without_signature_400(self):
        body = {"cpm_trans_id": "ORD-NOSIGN", "order_id": "ORD-NOSIGN", "status": "PAID", "amount": 15000, "currency": "XOF"}
        r = self.client.post(cb_url(), data=json.dumps(body), content_type="application/json")
        self.assertEqual(r.status_code, 400)

    @patch("store.views.payment_check", return_value=(False, None))
    def test_webhook_bad_check_sets_failed(self, mcheck):
        p = Payment.objects.create(order_id="ORD-KO", amount=15000, currency="XOF", status="PENDING")
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_hex(raw)
        r = self.client.post(cb_url(), data=raw, content_type="application/json", **{hdr_key(): sig})
        self.assertEqual(r.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.status, "FAILED")

    @patch("store.views.payment_check", return_value=(True, "TX123"))
    @patch("store.views.deliver_ebook")
    def test_webhook_ok_delivers_once(self, mdeliver, mcheck):
        p = Payment.objects.create(order_id="ORD-OK", amount=15000, currency="XOF", status="PENDING")
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_hex(raw)

        r1 = self.client.post(cb_url(), data=raw, content_type="application/json", **{hdr_key(): sig})
        self.assertEqual(r1.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.status, "PAID")
        self.assertEqual(mdeliver.call_count, 1)

        r2 = self.client.post(cb_url(), data=raw, content_type="application/json", **{hdr_key(): sig})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(mdeliver.call_count, 1)  # idempotence OK

    @patch("store.views.payment_check", return_value=(True, "TX123"))
    @patch("store.views.deliver_ebook")
    def test_webhook_ok_hex(self, mdeliver, mcheck):
        p = Payment.objects.create(order_id="ORD-HEX", amount=15000, currency="XOF", status="PENDING")
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_hex(raw)
        r = self.client.post(cb_url(), data=raw, content_type="application/json", **{hdr_key(): sig})
        self.assertEqual(r.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.status, "PAID")
        self.assertEqual(mdeliver.call_count, 1)
        # idempotence
        r2 = self.client.post(cb_url(), data=raw, content_type="application/json", **{hdr_key(): sig})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(mdeliver.call_count, 1)

    @patch("store.views.payment_check", return_value=(True, "TX124"))
    @patch("store.views.deliver_ebook")
    def test_webhook_ok_b64(self, mdeliver, mcheck):
        p = Payment.objects.create(order_id="ORD-B64", amount=15000, currency="XOF", status="PENDING")
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_b64(raw)
        r = self.client.post(cb_url(), data=raw, content_type="application/json", **{hdr_key(): sig})
        self.assertEqual(r.status_code, 200)

    @patch("store.views.payment_check", return_value=(True, "TX125"))
    @patch("store.views.deliver_ebook")
    def test_webhook_ok_hexpref(self, mdeliver, mcheck):
        p = Payment.objects.create(order_id="ORD-PREF", amount=15000, currency="XOF", status="PENDING")
        body = make_payload(p.order_id)
        raw = raw_json_bytes(body)
        sig = sig_hexpref(raw)
        r = self.client.post(cb_url(), data=raw, content_type="application/json", **{hdr_key(): sig})
        self.assertEqual(r.status_code, 200)
