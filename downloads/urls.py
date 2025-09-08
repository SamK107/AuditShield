from django.urls import path
from .views import (
    asset_download, asset_upload, asset_upload_success, telecharger
)

app_name = "downloads"
urlpatterns = [
    path("<slug:slug>/", asset_download, name="asset_download"),
    path("upload/", asset_upload, name="asset_upload"),
    path("upload/success/", asset_upload_success, name="asset_upload_success"),
    path(
        "telecharger/<slug:slug>/", telecharger, name="telecharger"
    ),
]