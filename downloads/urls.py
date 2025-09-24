from django.urls import path

from . import views

app_name = "downloads"

urlpatterns = [
    path("<slug:slug>/", views.asset_download, name="asset_download"),
]