from django.urls import path

from . import views

app_name = "downloads_public"

urlpatterns = [
    path(
        "checklists/",
        views.category_page,
        {"slug": "checklists"},
        name="page_checklists",
    ),
    path(
        "bonus/",
        views.category_page,
        {"slug": "bonus"},
        name="page_bonus",
    ),
    path(
        "outils-pratiques/",
        views.category_page,
        {"slug": "outils-pratiques"},
        name="page_outils",
    ),
    path(
        "irregularites/",
        views.category_page,
        {"slug": "irregularites"},
        name="page_irregularites",
    ),
    path(
        "claim-access/",
        views.claim_access,
        name="claim_access",
    ),
]
