# store/tests/test_orange_money.py
import json
import os
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from store.models import Order, Product, ClientInquiry


class TestOrangeMoneyMock(TestCase):
    def setUp(self):
        self.client = Client()
        # Activer le mode mock
        os.environ["OM_SANDBOX_MOCK"] = "1"
        os.environ["OM_MERCHANT_KEY"] = ""  # Vide pour forcer le mock

    def test_create_checkout_mock_mode(self):
        """Test que create_checkout retourne une URL mock en mode sandbox."""
        from store.services import orange_money

        # Créer un request mock
        class MockRequest:
            scheme = "http"
            get_host = lambda self: "127.0.0.1:8000"

        request = MockRequest()
        payment_url, order_id = orange_money.create_checkout(
            inquiry_id=1,
            amount=48090,
            currency="XOF",
            request=request,
        )

        # Vérifier que l'URL est une URL mock locale
        self.assertIn("/payments/om/mock/", payment_url)
        self.assertIn("transaction_id=", payment_url)
        self.assertTrue(order_id.startswith("OM-SBX-"))

    def test_om_mock_checkout_page(self):
        """Test que la page mock s'affiche correctement."""
        tx = "OM-SBX-TEST123"
        response = self.client.get(
            reverse("store:om_mock_checkout"),
            {"transaction_id": tx}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Orange Money", response.content)
        self.assertIn(tx.encode(), response.content)

    def test_om_mock_confirm_success(self):
        """Test la simulation d'un paiement réussi."""
        # Créer un produit et une commande
        product = Product.objects.create(
            slug="test-product",
            title="Test Product",
            price_fcfa=48090,
            is_published=True,
        )
        order = Order.objects.create(
            product=product,
            email="test@example.com",
            amount_fcfa=48090,
            currency="XOF",
            status="CREATED",
            provider_ref="OM-SBX-TEST123",
        )

        response = self.client.post(
            reverse("store:om_mock_confirm"),
            {
                "transaction_id": "OM-SBX-TEST123",
                "action": "success",
            },
        )

        # Vérifier la redirection
        self.assertIn(response.status_code, [200, 302])
        order.refresh_from_db()
        self.assertEqual(order.status, Order.PAID)

    def test_om_mock_confirm_failed(self):
        """Test la simulation d'un paiement échoué."""
        product = Product.objects.create(
            slug="test-product",
            title="Test Product",
            price_fcfa=48090,
            is_published=True,
        )
        order = Order.objects.create(
            product=product,
            email="test@example.com",
            amount_fcfa=48090,
            currency="XOF",
            status="CREATED",
            provider_ref="OM-SBX-TEST456",
        )

        response = self.client.post(
            reverse("store:om_mock_confirm"),
            {
                "transaction_id": "OM-SBX-TEST456",
                "action": "failed",
            },
        )

        self.assertIn(response.status_code, [200, 302])
        order.refresh_from_db()
        self.assertEqual(order.status, Order.FAILED)

    def test_om_notify_success(self):
        """Test le webhook om_notify avec un statut SUCCESS."""
        product = Product.objects.create(
            slug="test-product",
            title="Test Product",
            price_fcfa=48090,
            is_published=True,
        )
        order = Order.objects.create(
            product=product,
            email="test@example.com",
            amount_fcfa=48090,
            currency="XOF",
            status="CREATED",
            provider_ref="OM-ORDER123",
        )

        payload = {
            "order_id": "OM-ORDER123",
            "status": "SUCCESS",
            "txnid": "OM-TXN-123",
        }

        response = self.client.post(
            reverse("store:om_notify"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.PAID)

    def test_om_notify_failed(self):
        """Test le webhook om_notify avec un statut FAILED."""
        product = Product.objects.create(
            slug="test-product",
            title="Test Product",
            price_fcfa=48090,
            is_published=True,
        )
        order = Order.objects.create(
            product=product,
            email="test@example.com",
            amount_fcfa=48090,
            currency="XOF",
            status="CREATED",
            provider_ref="OM-ORDER456",
        )

        payload = {
            "order_id": "OM-ORDER456",
            "status": "FAILED",
            "txnid": "OM-TXN-456",
        }

        response = self.client.post(
            reverse("store:om_notify"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.FAILED)

    def test_om_notify_missing_order_id(self):
        """Test le webhook om_notify sans order_id."""
        payload = {
            "status": "SUCCESS",
        }

        response = self.client.post(
            reverse("store:om_notify"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_om_notify_order_not_found(self):
        """Test le webhook om_notify avec un order_id inexistant."""
        payload = {
            "order_id": "OM-NOTFOUND",
            "status": "SUCCESS",
        }

        response = self.client.post(
            reverse("store:om_notify"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_om_return_page(self):
        """Test la page de retour om_return."""
        product = Product.objects.create(
            slug="test-product",
            title="Test Product",
            price_fcfa=48090,
            is_published=True,
        )
        order = Order.objects.create(
            product=product,
            email="test@example.com",
            amount_fcfa=48090,
            currency="XOF",
            status="PAID",
            provider_ref="OM-ORDER789",
        )

        response = self.client.get(
            reverse("store:om_return"),
            {"order_id": "OM-ORDER789"},
        )

        self.assertEqual(response.status_code, 200)

