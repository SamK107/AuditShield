# store/urls.py
from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("ebook/<slug:slug>/", views.product_detail, name="product_detail"),
    path("offres/", views.offers, name="offers"),
    path("exemples/", views.examples, name="examples"),

    path("buy/<slug:slug>/", views.buy, name="buy"),
    path("payment/return/", views.payment_return, name="payment_return"),
    path("payment/callback/", views.payment_callback, name="payment_callback"),
    path("telecharger/<uuid:token>/", views.download, name="download"),
]
