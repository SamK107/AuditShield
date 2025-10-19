from .base import *
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# DB locale (exemples)
# SQLITE:
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
# ou Postgres local via DATABASE_URL si tu préfères.

# Email en local : console ou MailHog/Mailpit
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
