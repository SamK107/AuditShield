from django.urls import path

from . import views

app_name = "downloads"

urlpatterns = [
    path("<slug:slug>/", views.asset_download, name="asset_download"),
    path("secure/<uuid:order_uuid>/", views.download_secure_view, name="secure"),
    path(
        "secure/<uuid:order_uuid>/<uuid:token>/",
        views.download_secure_with_token_view,
        name="secure_token",
    ),
    path("file/<int:asset_id>/", views.asset_serve_view, name="asset"),
]
