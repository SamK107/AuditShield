from .base import *
DEBUG = False
ALLOWED_HOSTS = ["auditsanspeur.com", "www.auditsanspeur.com"]

# Postgres prod via env
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("PG_DB"),
        "USER": os.getenv("PG_USER"),
        "PASSWORD": os.getenv("PG_PASSWORD"),
        "HOST": os.getenv("PG_HOST", "127.0.0.1"),
        "PORT": os.getenv("PG_PORT", "5432"),
    }
}

# Sécurité de base
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
