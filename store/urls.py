from django.urls import path, include
from . import views
from . import payment_views as pay
from . import views_admin_kit as views_admin_kit
from . import kit_views

app_name = "store"

urlpatterns = [
    # Checkout unifié (CinetPay + Orange Money)
    path("buy/<slug:slug>/", pay.start_checkout, name="buy"),
    path("buy/", pay.start_checkout, {"slug": "cinetpay"}, name="buy_default"),
    
    # Orange Money: checkout ebook (nouveau flux API réel)
    path("buy/om/<slug:product_slug>/", pay.orange_start_payment, name="orange_start"),
    # Orange Money: checkout ebook (legacy)
    path("buy/orange/<slug:product_slug>/", pay.orange_checkout, name="orange_checkout"),
    path("orange/mock/<str:provider_ref>/", pay.orange_mock_checkout, name="orange_mock_checkout"),
    path("orange/mock/<str:provider_ref>/success/", pay.orange_mock_success, name="orange_mock_success"),
    path("orange/mock/<str:provider_ref>/failure/", pay.orange_mock_failure, name="orange_mock_failure"),
    path("orange/callback/", pay.orange_callback, name="orange_callback"),
    path("orange/test/", pay.orange_api_test, name="orange_api_test"),
    
    # Orange Money: routes avec préfixe /store/ pour compatibilité
    path("store/orange/mock/<str:provider_ref>/", pay.orange_mock_checkout, name="orange_mock_checkout_store"),
    path("store/orange/mock/<str:provider_ref>/success/", pay.orange_mock_success, name="orange_mock_success_store"),
    path("store/orange/mock/<str:provider_ref>/failure/", pay.orange_mock_failure, name="orange_mock_failure_store"),
    path("store/orange/test/", pay.orange_api_test, name="orange_api_test_store"),
    
    # Orange Money: retours & webhook (nouveau flux API réel - conforme PDF)
    path("payments/om/return/", pay.orange_return, name="orange_return"),
    path("payments/om/notify/", pay.orange_notify, name="orange_notify"),
    # Orange Money: retours & webhook (legacy pour Kit - gardé pour compatibilité)
    path("payments/om/return-legacy/", pay.om_return, name="om_return"),
    path("payments/om/notify-legacy/", pay.om_notify, name="om_notify"),
    path("payments/om/mock/", pay.om_mock_checkout, name="om_mock_checkout"),
    path("payments/om/mock/confirm/", pay.om_mock_confirm, name="om_mock_confirm"),
    # Orange Money: démarrage paiement Kit complet
    path(
        "payments/kit/om/start/<int:inquiry_id>/",
        pay.kit_pay_om_start,
        name="kit_pay_om_start",
    ),
    # Orange Money: nouvelles routes modulaires (payments/orange_money/)
    path(
        "payments/",
        include(
            ("store.payments.orange_money.urls", "store"),
            namespace="orange_money",
        ),
    ),

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
        "kit-complet/demande/<int:pk>/",
        views_admin_kit.kit_complete_inquiry_detail,
        name="kit_complete_inquiry_detail",
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
    path(
        "kit-complet-traitement/<int:pk>/status/",
        views_admin_kit.kit_complete_status,
        name="kit_complete_status",
    ),
    path(
        "kit-complet/demande/<int:pk>/draft/",
        views_admin_kit.kit_generated_draft_download,
        name="kit_generated_draft_download",
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

    # Kit inquiry & paiement
    path("kit/inquiry/", views.kit_inquiry, name="kit_inquiry"),
    path(
        "kit/inquiry/<int:inquiry_id>/devis/",
        views.kit_inquiry_quote,
        name="kit_inquiry_quote",
    ),
    path(
        "kit/inquiry/<int:inquiry_id>/checkout/",
        views.kit_checkout,
        name="kit_checkout",
    ),
    path(
        "kit/inquiry/merci/",
        views.kit_inquiry_success,
        name="kit_inquiry_success",
    ),
    path(
        "kit/inquiry/<int:inquiry_id>/paiement-confirme/",
        views.kit_payment_success,
        name="kit_payment_success",
    ),

    # Training
    path(
        "training/inquiry/",
        views.training_inquiry,
        name="training_inquiry",
    ),

    # Kit Order Tracking & Success
    path(
        "kit/payment/success/<str:tracking_id>/",
        kit_views.kit_payment_success,
        name="kit_payment_success",
    ),
    path(
        "kit/track/<str:tracking_id>/",
        kit_views.kit_tracking,
        name="kit_tracking",
    ),
    path(
        "kit/starter-pack/",
        kit_views.kit_starter_pack_view,
        name="kit_starter_pack",
    ),
]
