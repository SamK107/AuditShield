from django.urls import path
from .views import asset_download

app_name = "downloads"
urlpatterns = [
    path("d/<slug:slug>/", asset_download, name="asset_download"),
]