import pytest
from django.urls import reverse

from store.models import Order
from store.tests.factories import OrderFactory
from store.tests.utils.status_helpers import coerce_status


@pytest.mark.django_db
def test_payment_return_denies_when_unpaid(client, mocker):
    order = OrderFactory(status=coerce_status(Order, "PENDING"))
    mocker.patch("store.services.cinetpay.check_transaction", return_value="failed")

    base_url = reverse("store:payment_return")
    tid = order.transaction_id  # noqa: E501
    query = f"?transaction_id={tid}"
    url = base_url + query
    resp = client.get(url)
    assert resp.status_code in (200, 302)  # selon design : page info/erreur ou redirect
    # Important : ne pas rediriger vers downloads si unpaid
    assert "downloads" not in resp.get("Location", "").lower()
