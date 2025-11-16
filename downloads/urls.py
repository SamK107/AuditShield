from django.urls import path

from . import views

app_name = "downloads"

urlpatterns = [
    path("<slug:slug>/", views.asset_download, name="asset_download"),
    path("resend-links/", views.resend_links, name="resend_links"),
    path(
        "secure/<uuid:order_uuid>/",
        views.download_secure_view,
        name="secure",
    ),
    path(
        "secure/<uuid:order_uuid>/resend/",
        views.resend_fulfilment_email,
        name="resend_fulfilment",
    ),
    path(
        "secure/<uuid:order_uuid>/<uuid:token>/",
        views.download_secure_with_token_view,
        name="secure_token",
    ),
    path("file/<int:asset_id>/", views.asset_serve_view, name="asset"),
    path(
        "resources/<uuid:order_uuid>/",
        views.resources_overview,
        name="resources",
    ),
]
