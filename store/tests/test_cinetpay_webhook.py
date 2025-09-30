# store/tests/test_cinetpay_webhook.py
import hashlib
import hmac
import json
import os

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from store.models import PaymentWebhookLog


class TestCinetPayWebhook(TestCase):
    def setUp(self):
        self.client = Client()
        # Assure des valeurs pendant le test (fallback si settings vides)
        os.environ.setdefault("CINETPAY_API_KEY", "test_api_key")
        os.environ.setdefault("CINETPAY_SECRET_KEY", "test_secret_key")

    def _sig(self, body: bytes) -> str:
        secret = (settings.CINETPAY_SECRET_KEY or settings.CINETPAY_API_KEY or "").encode("utf-8")
        return hmac.new(secret, body, hashlib.sha256).hexdigest()

    def test_notify_signed_success(self):
        payload = {"transaction_id": "ORDER-123", "status": "SUCCESS"}
        body = json.dumps(payload).encode("utf-8")
        sig = self._sig(body)
        res = self.client.post(
            reverse("store:cinetpay_notify"),
            data=body,
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": sig},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"OK", res.content)

        # Vérifier que le log a été créé
        log = PaymentWebhookLog.objects.filter(order_ref="ORDER-123").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "SUCCESS")
        self.assertTrue(log.processed)

    def test_notify_bad_signature(self):
        payload = {"transaction_id": "ORDER-456", "status": "FAILED"}
        body = json.dumps(payload).encode("utf-8")
        res = self.client.post(
            reverse("store:cinetpay_notify"),
            data=body,
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": "badbadbad"},
        )
        self.assertEqual(res.status_code, 400)

        # Vérifier que le log a été créé même avec signature invalide
        log = PaymentWebhookLog.objects.filter(order_ref="ORDER-456").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "FAILED")
        self.assertFalse(log.processed)
        self.assertEqual(log.http_status, 400)

    def test_notify_invalid_json(self):
        body = b"invalid json"
        sig = self._sig(body)
        res = self.client.post(
            reverse("store:cinetpay_notify"),
            data=body,
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": sig},
        )
        self.assertEqual(res.status_code, 400)

    def test_notify_get_method_not_allowed(self):
        res = self.client.get(reverse("store:cinetpay_notify"))
        self.assertEqual(res.status_code, 400)

    def test_notify_idempotence(self):
        """Test que les notifications dupliquées ne sont pas retraitées"""
        payload = {"transaction_id": "ORDER-DUPLICATE", "status": "SUCCESS"}
        body = json.dumps(payload).encode("utf-8")
        sig = self._sig(body)

        # Premier appel
        res1 = self.client.post(
            reverse("store:cinetpay_notify"),
            data=body,
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": sig},
        )
        self.assertEqual(res1.status_code, 200)

        # Vérifier qu'un log processed=True existe
        log_count_before = PaymentWebhookLog.objects.filter(
            order_ref="ORDER-DUPLICATE", status="SUCCESS", processed=True
        ).count()
        self.assertEqual(log_count_before, 1)

        # Deuxième appel (même payload)
        res2 = self.client.post(
            reverse("store:cinetpay_notify"),
            data=body,
            content_type="application/json",
            **{"HTTP_X_SIGNATURE": sig},
        )
        self.assertEqual(res2.status_code, 200)

        # Le deuxième log ne devrait pas être marqué processed=True
        # car already_ok=True empêche le retraitement
        total_logs = PaymentWebhookLog.objects.filter(order_ref="ORDER-DUPLICATE").count()
        self.assertEqual(total_logs, 2)  # Deux logs au total

        processed_logs = PaymentWebhookLog.objects.filter(
            order_ref="ORDER-DUPLICATE", processed=True
        ).count()
        self.assertEqual(processed_logs, 1)  # Mais un seul processed=True

    def test_return_page(self):
        res = self.client.get(reverse("store:cinetpay_return"))
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Paiement r\xc3\xa9ussi", res.content)

    def test_cancel_page(self):
        res = self.client.get(reverse("store:cinetpay_cancel"))
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Paiement annul\xc3\xa9", res.content)
