import pytest
from django.urls import reverse

from store.models import Order
from store.tests.factories import OrderFactory
from store.tests.utils.status_helpers import coerce_status


@pytest.mark.django_db
def test_callback_marks_order_paid_idempotently(client, mocker):
    order = OrderFactory(status=coerce_status(Order, "PENDING"))
    mocker.patch("store.services.cinetpay.verify_hmac", return_value=True)
    mocker.patch("store.services.cinetpay.check_transaction", return_value="paid")

    payload = {"transaction_id": order.transaction_id}
    # 1er POST
    resp1 = client.post(
        reverse("store:payment_callback"), data=payload, content_type="application/json"
    )
    assert resp1.status_code in (200, 204)

    order.refresh_from_db()
    assert str(order.status).lower() == "paid"

    # 2e POST identique (idempotent)
    resp2 = client.post(
        reverse("store:payment_callback"), data=payload, content_type="application/json"
    )
    assert resp2.status_code in (200, 204)
    # Si PaymentEvent existe, on pourrait vérifier l'absence de doublons ici
