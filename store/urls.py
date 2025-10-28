from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("buy/<slug:slug>/", views.buy, name="buy"),
    # par défaut, /buy/ redirige vers le produit via l'alias "cinetpay"
    path("buy/", views.buy, {"slug": "cinetpay"}, name="buy_default"),
    # ----- BONUS Kit de préparation -----
    path("bonus/kit-preparation/", views.bonus_kit_landing, name="bonus_landing"),
    path("bonus/kit-preparation/start", views.bonus_kit_start, name="bonus_submit"),
    path("bonus/kit-preparation/merci", views.bonus_kit_thanks, name="bonus_thanks"),

    # ----- (autres routes existantes) -----
    path("offres/", views.offers, name="offers"),
    path("exemples/", views.examples, name="examples"),
    path("exemples/preliminaires/", views.examples_prelim, name="examples_prelim"),
    path("exemples/blocs/", views.examples_block, name="examples_block"),
    path("produit/<slug:slug>/", views.product_detail, name="product_detail"),
    path("start-checkout/", views.start_checkout, name="start_checkout"),
    
    path(
        "buy/other-methods/<slug:product_key>/",
        views.buy_other_methods,
        name="buy_other_methods",
        ),
    path("kit/inquiry/", views.kit_inquiry, name="kit_inquiry"),
    path("training/inquiry/", views.training_inquiry, name="training_inquiry"),
]
