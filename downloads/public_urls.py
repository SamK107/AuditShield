from django.urls import path

from . import views
from .views_manual_claim import manual_claim

app_name = "downloads_public"

urlpatterns = [
    # Support URL without trailing slash for gating
    path("bonus", views.category_page, {"slug": "bonus"}),
    path(
        "bonus/",
        views.category_page,
        {"slug": "bonus"},
        name="category_bonus",
    ),
    path(
        "checklists/",
        views.category_page,
        {"slug": "checklists"},
        name="category_checklists",
    ),
    path(
        "outils-pratiques/",
        views.category_page,
        {"slug": "outils-pratiques"},
        name="category_outils",
    ),
    path(
        "irregularites/",
        views.category_page,
        {"slug": "irregularites"},
        name="category_irregs",
    ),
    path(
        "claim/",
        views.claim_access,
        name="claim_access",
    ),
    path(
        "claim/manual/",
        manual_claim,
        name="manual_claim",
    ),
]
