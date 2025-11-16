from django.urls import path
from . import views
from . import payment_views as pay
from . import views_admin_kit as views_admin_kit

app_name = "store"

urlpatterns = [
    # Checkout unifié (CinetPay + Orange Money)
    path("buy/<slug:slug>/", pay.start_checkout, name="buy"),
    path("buy/", pay.start_checkout, {"slug": "cinetpay"}, name="buy_default"),
    # Orange Money: retours & webhook + sandbox mock
    path("payments/om/return/", pay.om_return, name="om_return"),
    path("payments/om/notify/", pay.om_notify, name="om_notify"),
    path("payments/om/mock/", pay.om_mock_checkout, name="om_mock_checkout"),
    # CinetPay: retours & webhook
    path(
        "payments/cinetpay/return/",
        views.cinetpay_return,
        name="cinetpay_return",
    ),
    path(
        "payments/cinetpay/notify/",
        views.cinetpay_notify,
        name="cinetpay_notify",
    ),
    path(
        "payments/cinetpay/mock/",
        pay.cinetpay_mock_checkout,
        name="cinetpay_mock_checkout",
    ),
    # Backoffice Kit Complet
    path(
        "kit-complet-traitement/",
        views_admin_kit.kit_complete_processing_list,
        name="kit_complete_processing",
    ),
    path(
        "kit-complet-traitement/<int:pk>/process/",
        views_admin_kit.kit_complete_process,
        name="kit_complete_process",
    ),
    path(
        "kit-complet-traitement/<int:pk>/upload/",
        views_admin_kit.kit_complete_upload,
        name="kit_complete_upload",
    ),
    path(
        "kit-complet-traitement/<int:pk>/publish/",
        views_admin_kit.kit_complete_publish,
        name="kit_complete_publish",
    ),
    # Tarifs Kit complet
    path("tarifs/kit-complet/", views.tariffs_kit, name="tariffs_kit"),
    path("api/estimate-kit/", views.estimate_kit, name="estimate_kit"),
    # ----- BONUS Kit de préparation -----
    path(
        "bonus/kit-preparation/",
        views.bonus_kit_landing,
        name="bonus_landing",
    ),
    path(
        "bonus/kit-preparation/start",
        views.bonus_kit_start,
        name="bonus_submit",
    ),
    path(
        "bonus/kit-preparation/merci",
        views.bonus_kit_thanks,
        name="bonus_thanks",
    ),

    # ----- (autres routes existantes) -----
    path("offres/", views.offers, name="offers"),
    path("exemples/", views.examples, name="examples"),
    path(
        "exemples/preliminaires/",
        views.examples_prelim,
        name="examples_prelim",
    ),
    path(
        "exemples/blocs/",
        views.examples_block,
        name="examples_block",
    ),
    path(
        "produit/<slug:slug>/",
        views.product_detail,
        name="product_detail",
    ),
    path(
        "start-checkout/",
        views.start_checkout,
        name="start_checkout",
    ),

    path(
        "buy/other-methods/<slug:product_key>/",
        views.buy_other_methods,
        name="buy_other_methods",
        ),
    path("kit/inquiry/", views.kit_inquiry, name="kit_inquiry"),
    path(
        "kit/inquiry/merci/",
        views.kit_inquiry_success,
        name="kit_inquiry_success",
    ),
    path(
        "training/inquiry/",
        views.training_inquiry,
        name="training_inquiry",
    ),
]
