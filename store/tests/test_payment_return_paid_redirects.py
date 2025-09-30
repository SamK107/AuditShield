from decimal import Decimal

import pytest
from django.urls import reverse

from store.models import Order
from store.tests.factories import OrderFactory, ProductFactory
from store.tests.utils.status_helpers import coerce_status


@pytest.mark.django_db
def test_payment_return_redirects_to_secure_downloads_when_paid(client, mocker):
    product = ProductFactory()
    order = OrderFactory(
        product=product, status=coerce_status(Order, "PENDING"), amount_fcfa=Decimal("15000")
    )
    mocker.patch("store.services.cinetpay.check_transaction", return_value="paid")

    base_url = reverse("store:payment_return")
    tid = order.transaction_id  # noqa: E501
    query = f"?transaction_id={tid}"
    url = base_url + query
    resp = client.get(url)
    assert resp.status_code in (302, 303)
    assert "downloads" in resp["Location"].lower()
