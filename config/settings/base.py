from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only")
DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    # tes apps
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Email (valeurs par défaut, spécialisées en dev/prod)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("SMTP_HOST", "")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("SMTP_TLS", "1") == "1"

# Variables IMAP (spécialisées en dev/prod)
RECEIPTS_IMAP_HOST = os.getenv("RECEIPTS_IMAP_HOST", "")
RECEIPTS_IMAP_PORT = int(os.getenv("RECEIPTS_IMAP_PORT", "993"))
RECEIPTS_IMAP_USER = os.getenv("RECEIPTS_IMAP_USER", "")
RECEIPTS_IMAP_PASSWORD = os.getenv("RECEIPTS_IMAP_PASSWORD", "")
ENABLE_BONUS_KIT = os.getenv("ENABLE_BONUS_KIT", "0") == "1"
