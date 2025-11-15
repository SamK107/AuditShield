"""
Configuration de base Django - partagée entre dev et prod
"""
from pathlib import Path
import importlib.util
from environs import Env
import os

# -----------------------------------------------------------------------------
# Base & .env
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

env = Env()
# Lecture du fichier .env à la racine
env.read_env(path=str(BASE_DIR / ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def _clean_env_value(value):
    """Nettoie une valeur d'environnement en ignorant les commentaires."""
    if not value:
        return None
    value = value.strip()
    # Ignorer si la valeur commence par #
    if value.startswith('#'):
        return None
    # Extraire la partie avant le # (si commentaire inline)
    if '#' in value:
        value = value.split('#')[0].strip()
    return value if value else None


# Nettoyer les valeurs pour ignorer les commentaires et espaces
_openai_org = os.getenv("OPENAI_ORG", "")
OPENAI_ORG = _clean_env_value(_openai_org)

_openai_project = os.getenv("OPENAI_PROJECT", "")
OPENAI_PROJECT = _clean_env_value(_openai_project)

_openai_base_url = os.getenv("OPENAI_BASE_URL", "")
OPENAI_BASE_URL = _clean_env_value(_openai_base_url)

# Choix du modèle principal + fallback(s)
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_CHAT_MODEL_FALLBACKS = [
    "gpt-4o",        # priorité 2
    "gpt-4o-mini",   # priorité 3 (au cas où tu changes le principal)
]

# -----------------------------------------------------------------------------
# Debug / Secret
# -----------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", False)
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="dev-insecure-key")

# -----------------------------------------------------------------------------
# Allowed Hosts & CSRF Trusted Origins
# -----------------------------------------------------------------------------
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    ["http://127.0.0.1:8000", "http://localhost:8000"],
)

# -----------------------------------------------------------------------------
# Applications
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Applications du projet
    "core",
    "store",
    "downloads",
    "legal",
]

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
USE_WHITENOISE = env.bool("USE_WHITENOISE", True)
HAS_WHITENOISE = importlib.util.find_spec("whitenoise") is not None

MIDDLEWARE = ["django.middleware.security.SecurityMiddleware"]

if USE_WHITENOISE and HAS_WHITENOISE:
    MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")

MIDDLEWARE += [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------------------------------------------------------------------
# URL / WSGI / ASGI
# -----------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# -----------------------------------------------------------------------------
# Static / Media
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Médias privés (fichiers payants)
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"

# Stockage (avec WhiteNoise si disponible)
if USE_WHITENOISE and HAS_WHITENOISE:
    STORAGES = {
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage.CompressedManifestStaticFilesStorage"
            ),
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    }
else:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    }

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Bamako"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Email (valeurs par défaut, surchargées en dev/prod)
# -----------------------------------------------------------------------------
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env.str("EMAIL_HOST", "localhost")
EMAIL_PORT = env.int("EMAIL_PORT", 587)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", False)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env.str(
    "DEFAULT_FROM_EMAIL",
    (
        f"Audit Sans Peur <{EMAIL_HOST_USER}>"
        if EMAIL_HOST_USER
        else "contact@auditsanspeur.com"
    ),
)
SERVER_EMAIL = env.str("SERVER_EMAIL", EMAIL_HOST_USER or "root@localhost")
# Expéditeur spécifique pour les emails de livraison (facultatif)
FULFILMENT_SENDER = env.str("FULFILMENT_SENDER", DEFAULT_FROM_EMAIL)

# -----------------------------------------------------------------------------
# CinetPay
# -----------------------------------------------------------------------------
CINETPAY_SITE_ID = env.str("CINETPAY_SITE_ID", default=None)
CINETPAY_API_KEY = env.str("CINETPAY_API_KEY", default=None)
CINETPAY_SECRET_KEY = env.str("CINETPAY_SECRET_KEY", default=None)
CINETPAY_MODE = env.str("CINETPAY_MODE", "PROD").upper()
CINETPAY_ENV = env.str("CINETPAY_ENV", "sandbox")

# -----------------------------------------------------------------------------
# Kit Complet - Configuration
# -----------------------------------------------------------------------------
import os
KIT_COVER_PATH = env.str(
    "KIT_COVER_PATH",
    os.path.join(BASE_DIR, "assets", "Kit_Complet_Preparation_Couverture_BSG.docx")
)
CINETPAY_BASE_URL = env.str(
    "CINETPAY_BASE_URL", "https://api-checkout.cinetpay.com/v2/payment"
)
CINETPAY_NOTIFY_URL = env.str(
    "CINETPAY_NOTIFY_URL", "http://127.0.0.1:8000/offres/notify/"
)
CINETPAY_RETURN_URL = env.str(
    "CINETPAY_RETURN_URL", "http://127.0.0.1:8000/offres/retour/"
)
CINETPAY_CANCEL_URL = env.str(
    "CINETPAY_CANCEL_URL", "http://127.0.0.1:8000/offres/cancel/"
)

# -----------------------------------------------------------------------------
# Bonus Kit
# -----------------------------------------------------------------------------
ENABLE_BONUS_KIT = env.bool("ENABLE_BONUS_KIT", False)

# -----------------------------------------------------------------------------
# Liens d'achat externes
# -----------------------------------------------------------------------------
EXTERNAL_BUY_LINKS_NOTE = (
    "Après achat, l'ebook contient des liens sécurisés vers vos bonus "
    "sur auditsanspeur.com."
)

EXTERNAL_BUY_LINKS = {
    "produit": {
        "publiseer": {
            "label": "Publiseer",
            "url": "https://publiseer.com/ta-page-produit",
            "badge": "Recommandé",
            "description": "Distribution mondiale (Amazon, Google, Apple).",
            "logo": "/static/partners/publiseer.svg",
        },
        "youscribe": {
            "label": "YouScribe Afrique",
            "url": "https://youscribe.com/ta-page-produit",
            "description": "Portée Afrique francophone.",
            "logo": "/static/partners/youscribe.svg",
        },
        "chariow": {
            "label": "Chariow",
            "url": "https://chariow.com/ta-page-produit",
            "description": "Extension régionale.",
            "logo": "/static/partners/chariow.svg",
        },
    }
}
for _alias in ("produit", "audit-services-publics", "ebook-audit-sans-peur"):
    EXTERNAL_BUY_LINKS[_alias] = EXTERNAL_BUY_LINKS["produit"]

# -----------------------------------------------------------------------------
# Celery, OpenAI, Site URL Configuration
# Chargées depuis config/settings/__init__.py (utilise python-dotenv)
# Le .env est déjà chargé dans __init__.py, on peut utiliser os.getenv ou importer
# -----------------------------------------------------------------------------
import os
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")
