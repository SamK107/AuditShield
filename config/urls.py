from django.urls import path
from core.views_debug import healthcheck_view, whoami_view
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

# config/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    
    path("", include(("core.urls", "core"), namespace="core")),
     
     
    path("admin/", admin.site.urls),
    # Pages publiques de téléchargement (en racine)
    path(
        "",
        include(("downloads.public_urls", "downloads_public"), namespace="downloads_public"),
    ),
    # Route technique /downloads/<slug> pour servir les fichiers par slug
    path(
        "downloads/",
        include(("downloads.urls", "downloads"), namespace="downloads"),
    ),
    # Apps existantes
    # path(
    #     "",
    #     include(("core.urls", "core"), namespace="core"),
    # ),
    path(
        "",
        include(("store.urls", "store"), namespace="store"),
    ),
    path(
        "",
        include(("legal.urls", "legal"), namespace="legal"),
    ),
    
  
]

# Servir les fichiers médias en dev (PDF, images, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Optionnel : servir aussi les statiques via Django en dev (en prod, Whitenoise s'en charge)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
