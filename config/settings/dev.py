import os
from pathlib import Path
from dotenv import load_dotenv

"""
Configuration Django pour l'environnement de développement
"""


# === DEBUG & HOSTS ===
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '[::1]']

# === CHARGEMENT DU .env EN DEV ===
# dev.py est dans config/settings → le dossier projet (avec manage.py et .env) est parents[2]
PROJECT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_DIR / ".env")

from .base import *
# === BASE DE DONNÉES (PostgreSQL) ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('DB_NAME', 'auditshield'),        # noqa: F405
        'USER': env.str('DB_USER', 'postgres'),           # noqa: F405
        'PASSWORD': env.str('DB_PASSWORD', 'tata1000@'),  # noqa: F405
        'HOST': env.str('DB_HOST', '127.0.0.1'),          # noqa: F405
        'PORT': env.int('DB_PORT', 5432),                 # noqa: F405
        'CONN_MAX_AGE': 300,
    }
}

# === TEMPLATES ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # noqa: F405
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# === CACHE (désactivé en dev) ===
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# === SÉCURITÉ (relâchée en dev) ===
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# === EMAILS EN CONSOLE EN DEV ===
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "contact@auditsanspeur.com")

# Compatibilité: si BONUS_DESTINATION_EMAIL est défini, il domine CONTACT_INBOX_EMAIL
CONTACT_INBOX_EMAIL = os.environ.get(
    "BONUS_DESTINATION_EMAIL",
    os.environ.get("CONTACT_INBOX_EMAIL", "contact@auditsanspeur.com")
)
RECEIPTS_INBOX_EMAIL = os.environ.get("RECEIPTS_INBOX_EMAIL", "receipts@auditsanspeur.com")
UPLOAD_MAX_BYTES = int(os.environ.get("UPLOAD_MAX_BYTES", "5242880"))

SITE_BASE_URL = "http://127.0.0.1:8000"

# === CELERY : TÂCHES SYNCHRONES EN DEV ===
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# === IMAP RECEIPTS (pour fetch_receipts) ===
RECEIPTS_IMAP_HOST = os.environ.get("RECEIPTS_IMAP_HOST")
RECEIPTS_IMAP_PORT = int(os.environ.get("RECEIPTS_IMAP_PORT", "993"))
RECEIPTS_IMAP_SSL = str(os.environ.get("RECEIPTS_IMAP_SSL", "true")).lower() in ("1", "true", "yes")
RECEIPTS_IMAP_USER = os.environ.get("RECEIPTS_IMAP_USER")
RECEIPTS_IMAP_PASSWORD = os.environ.get("RECEIPTS_IMAP_PASSWORD")
RECEIPTS_IMAP_FOLDER = os.environ.get("RECEIPTS_IMAP_FOLDER", "INBOX")

# === LOGGING DÉTAILLÉ EN DEV (inclut Orange Money) ===
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },

    # Logger racine (tout ce qui n'a pas de logger spécifique)
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },

    'loggers': {
        # Logs Django généraux
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        # Requêtes SQL (très verbeux en DEBUG)
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        # 🔴 Logger spécifique pour ton service Orange Money
        'store.services.orange_money': {
            'handlers': ['console'],
            'level': 'DEBUG',   # DEBUG pour voir tous les détails (payload, réponses, etc.)
            'propagate': False,
        },
    },
}

# === ORANGE MONEY WEBPAY DEV CONFIGURATION ===
from dataclasses import dataclass

@dataclass
class OrangeMoneyConfig:
    env: str
    base_url: str
    merchant_msisdn: str
    merchant_code: str
    login: str
    password: str
    test_subscriber_msisdn: str
    currency: str
    country: str
    callback_url: str
    return_success_url: str
    return_failure_url: str

ORANGE_MONEY = OrangeMoneyConfig(
    env=os.getenv("OM_ENV", "sandbox"),
    base_url=os.getenv("OM_BASE_URL", "https://api.orange.com/orange-money-webpay/dev"),
    merchant_msisdn=os.getenv("OM_MERCHANT_MSISDN", ""),
    merchant_code=os.getenv("OM_MERCHANT_CODE", ""),
    login=os.getenv("OM_LOGIN", ""),
    password=os.getenv("OM_PASSWORD", ""),
    test_subscriber_msisdn=os.getenv("OM_TEST_SUBSCRIBER_MSISDN", "77011011234"),
    currency=os.getenv("OM_CURRENCY", "XOF"),
    country=os.getenv("OM_COUNTRY", "ML"),
    callback_url=os.getenv("OM_CALLBACK_URL", "http://127.0.0.1:8000/store/orange/callback/"),
    return_success_url=os.getenv("OM_RETURN_SUCCESS_URL", "http://127.0.0.1:8000/store/orange/success/"),
    return_failure_url=os.getenv("OM_RETURN_FAILURE_URL", "http://127.0.0.1:8000/store/orange/failure/"),
)
