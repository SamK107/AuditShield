from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("ebook/<slug:slug>/", views.product_detail, name="product_detail"),
    path("offres/", views.offers, name="offers"),

    # Formulaires demandes
    path("offres/kit/demande/", views.kit_inquiry, name="kit_inquiry"),
    path("offres/formation/demande/", views.training_inquiry_view, name="training_inquiry"),

    path("exemples/", views.examples, name="examples"),
    path("exemples-prelim/", views.examples_prelim, name="examples_prelim"),
    path("exemples/block", views.examples_block, name="examples_block"),

    path("buy/<slug:slug>/", views.buy, name="buy"),
    path("payment/return/", views.payment_return, name="payment_return"),
    # path("payment/callback/", views.payment_callback, name="payment_callback"),  # Ancienne route
    path("telecharger/<uuid:token>/", views.download, name="download"),

    # --- Paiement CinetPay sécurisé ---
    path("buy/<slug:product_slug>/<int:tier_id>/", views.start_checkout, name="start_checkout"),
    path("payment/return/", views.payment_return, name="payment_return"),
    path("payment/callback/", views.cinetpay_callback, name="cinetpay_callback"),

    path(
        "formation-assistance/demande/",
        views.training_inquiry_view,
        name="training_inquiry",
    ),
    path(
        "formation-assistance/merci/",
        views.training_inquiry_success,
        name="training_inquiry_success",
    ),
    path(
        "offres/kit/merci/",
        views.kit_inquiry_success,
        name="kit_inquiry_success",
    ),
]
