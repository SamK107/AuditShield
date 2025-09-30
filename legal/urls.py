from django.urls import path

from . import views

app_name = "legal"

urlpatterns = [
    path(
        "mentions-legales/", views.LegalPageView.as_view(slug="mentions-legales"), name="mentions"
    ),
    path("privacy/", views.LegalPageView.as_view(slug="privacy"), name="privacy"),
    path("cookies/", views.LegalPageView.as_view(slug="cookies"), name="cookies"),
    path("mentions-legales/modal/", views.mentions_modal, name="mentions_modal"),
]
