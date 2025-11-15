"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("core.urls", "core"), namespace="core")),
    # Specific fallback for test link to extrait
    path(
        "downloads/extrait-audit-sans-peur/",
        lambda request: redirect("/", permanent=False),
        name="downloads_extrait_fallback",
    ),
    # Pages publiques de téléchargement (en racine)
    path(
        "",
        include(
            ("downloads.public_urls", "downloads_public"),
            namespace="downloads_public"
        ),
    ),
    # Route technique /downloads/<slug>
    path(
        "downloads/",
        include(("downloads.urls", "downloads"), namespace="downloads"),
    ),
    path(
        "",
        include(("store.urls", "store"), namespace="store"),
    ),
    path(
        "",
        include(("legal.urls", "legal"), namespace="legal"),
    ),
    # Redirection legacy: anciens liens médias d'extraits
    # vers la route /downloads/<slug>/
    path(
        "media/extraits/<slug:slug>.pdf",
        lambda request, slug: redirect(
            "downloads:asset_download", slug=slug, permanent=True
        ),
        name="legacy_extract_redirect",
    ),
]

# Servir les fichiers médias en dev (PDF, images, etc.)
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

# Custom error handlers
handler404 = "core.views.custom_404"
handler500 = "core.views.custom_500"
