from django.urls import path
from . import views

app_name = "downloads_public"

urlpatterns = [
    path("bonus/kit-preparation/start", views.kit_preparation_start, name="kit_preparation_start"),
    path("bonus/kit-preparation/thanks", views.kit_preparation_thanks, name="kit_preparation_thanks"),
]
