# core/urls.py
from django.urls import path, include

from . import views

app_name = "core"

urlpatterns = [
    path("", views.coming_soon, name="coming_soon"),
    path("accueil/", views.home, name="home"),

    # Pages de téléchargement (namespacées)
    path("", include("downloads.public_urls", namespace="downloads")),
    path("a-propos/", views.about, name="about"),
    path("politique/", views.policy, name="policy"),
    path("cgv/", views.cgv, name="cgv"),
    path("contact/", views.contact, name="contact"),

    path("waitlist/", views.waitlist_signup, name="waitlist_signup"),

    # TEMP: Test route for 500 error (remove in production)
    path("boom/", views.boom, name="boom"),
]
