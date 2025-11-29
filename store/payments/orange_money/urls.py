"""
URLs pour Orange Money Mali.
"""
from django.urls import path
from . import views

app_name = "orange_money"

urlpatterns = [
    # Initiation d'un paiement
    path(
        "orange/start/order/<int:order_id>/",
        views.start_orange_payment,
        {"order_id": None},
        name="orange_start_order",
    ),
    path(
        "orange/start/inquiry/<int:inquiry_id>/",
        views.start_orange_payment,
        {"inquiry_id": None},
        name="orange_start_inquiry",
    ),
    # Callback/webhook (notify_url)
    path(
        "orange/notify/",
        views.orange_payment_notify,
        name="orange_notify",
    ),
    # Retours utilisateur
    path(
        "orange/success/",
        views.orange_payment_success,
        name="orange_success",
    ),
    path(
        "orange/failed/",
        views.orange_payment_failed,
        name="orange_failed",
    ),
]

