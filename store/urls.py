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
    path("payment/callback/", views.payment_callback, name="payment_callback"),
    path("telecharger/<uuid:token>/", views.download, name="download"),

    path("formation-assistance/demande/", views.training_inquiry_view, name="training_inquiry"),
    path("formation-assistance/merci/", views.training_inquiry_success, name="training_inquiry_success"),
    path("offres/kit/merci/", views.kit_inquiry_success, name="kit_inquiry_success"),
]
