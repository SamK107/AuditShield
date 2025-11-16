import os
import pytest
from django.test import Client, override_settings
from django.urls import reverse

from store.models import Product, Order


@pytest.mark.django_db
@override_settings(CINETPAY_MOCK=True, DEBUG=True)
def test_cinetpay_mock_checkout_and_return():
    # Activer aussi via env pour les chemins qui lisent os.getenv
    os.environ["CINETPAY_MOCK"] = "1"

    client = Client()
    product = Product.objects.create(
        title="Ebook Test",
        slug="ebook-test",
        price_fcfa=1000,
        is_published=True,
    )

    # 1) Init paiement (POST sur la vue start_checkout)
    resp = client.post(
        reverse("store:buy", args=[product.slug]),
        {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "70000000",
            "provider": "cinetpay",
        },
    )
    assert resp.status_code == 302
    assert "mock.cinetpay.test/checkout" in resp["Location"]

    # 2) Récupérer l'Order et simuler le retour navigateur
    order = Order.objects.latest("created_at")
    tx = order.provider_ref or order.cinetpay_payment_id or ""
    assert tx != ""

    return_url = reverse("store:cinetpay_return")
    resp2 = client.get(f"{return_url}?transaction_id={tx}")
    assert resp2.status_code in (302, 200)

    order.refresh_from_db()
    # En DEBUG + mock, payment_check renvoie always True → order doit être payé
    assert order.is_paid


