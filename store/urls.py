# store/urls.py
from django.urls import path
from . import views
from store.views import debug_host_view

app_name = "store"

urlpatterns = [
    # --- Pages "téléchargement" citées dans l’ebook ---
    path("checklists", views.downloads_checklists, name="downloads_checklists"),
    path("bonus", views.downloads_bonus, name="downloads_bonus"),
    path("bonus/", views.downloads_bonus, name="downloads_bonus_slash"),
    path("outils-pratiques", views.downloads_outils, name="downloads_outils"),
    path("irregularites", views.downloads_irregularites, name="downloads_irregularites"),

    # --- Pages publiques / offres ---
    path("offres/", views.offers, name="offers"),
    path("ebook/<slug:slug>/", views.product_detail, name="product_detail"),

    # --- Exemples (uniformisation des slashes) ---
    path("exemples/", views.examples, name="examples"),
    path("exemples-prelim/", views.examples_prelim, name="examples_prelim"),
    path("exemples/block/", views.examples_block, name="examples_block"),

    # --- Achat / Checkout (ordre important : spécifique AVANT générique) ---
    path("buy/<slug:product_slug>/<int:tier_id>/", views.start_checkout, name="start_checkout"),
    path("buy/<slug:slug>/", views.buy, name="buy"),

    # --- Paiement générique (ancien flux si encore utilisé) ---
    path("payment/return/", views.payment_return, name="payment_return"),
    # path("payment/callback/", views.cinetpay_callback, name="cinetpay_callback"),

    # --- CinetPay (endpoints principaux – ceux de ton .env) ---
    path("offres/notify/", views.cinetpay_notify, name="cinetpay_notify_offres"),
    path("offres/retour/", views.cinetpay_return, name="cinetpay_return_offres"),

    # --- CinetPay (alias – si référencés ailleurs) ---
    path("payments/cinetpay/notify/", views.cinetpay_notify, name="cinetpay_notify"),
    path("payments/cinetpay/return/", views.cinetpay_return, name="cinetpay_return"),
    path("payments/cinetpay/cancel/", views.cinetpay_cancel, name="cinetpay_cancel"),
    path("cinetpay/return/", views.cinetpay_return, name="cinetpay_return"),
    path("cinetpay/cancel/", views.cinetpay_cancel, name="cinetpay_cancel"),


    # --- Téléchargements ---
    path("telecharger/<uuid:token>/", views.download, name="download"),
    path("download-options/<uuid:token>/", views.download_options, name="download_options"),
    path("download/<uuid:token>/<str:version>/", views.download_version, name="download_version"),

    # --- Formulaires & remerciements ---
    path("offres/kit/demande/", views.kit_inquiry, name="kit_inquiry"),
    path("offres/kit/merci/", views.kit_inquiry_success, name="kit_inquiry_success"),
    path("formation-assistance/demande/", views.training_inquiry_view, name="training_inquiry"),
    path("formation-assistance/merci/", views.training_inquiry_success, name="training_inquiry_success"),
    path("__whoami__", views.debug_host_view, name="whoami"),
    
    #secure download
    path("downloads/secure/<int:asset_id>/", views.secure_download, name="secure_download"),
]
