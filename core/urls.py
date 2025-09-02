# core/urls.py
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("a-propos/", views.about, name="about"),
    path("politique/", views.policy, name="policy"),
    path("cgv/", views.cgv, name="cgv"),
    path("contact/", views.contact, name="contact"),
]
