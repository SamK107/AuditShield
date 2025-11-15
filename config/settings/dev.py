import os
from pathlib import Path
from dotenv import load_dotenv
"""
Configuration Django pour l'environnement de développement
"""
from .base import *  # noqa: F403, F401

# Surcharge pour le développement
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Email backend pour le développement (affichage en console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Base de données PostgreSQL pour le développement
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('DB_NAME', 'auditshield'),  # noqa: F405
        'USER': env.str('DB_USER', 'postgres'),  # noqa: F405
        'PASSWORD': env.str('DB_PASSWORD', 'tata1000@'),  # noqa: F405
        'HOST': env.str('DB_HOST', '127.0.0.1'),  # noqa: F405
        'PORT': env.int('DB_PORT', 5432),  # PostgreSQL 17 utilise souvent le port 5433
        # Désactivé en dev pour éviter les problèmes de connexion
        'CONN_MAX_AGE': 300,
    }
}

# Templates avec mode debug
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

# Désactiver la mise en cache en développement
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Sécurité désactivée en développement
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# Logging plus verbeux en développement
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'simple': {'format': '%(levelname)s: %(message)s'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            # Affiche les requêtes SQL en dev
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "contact@auditsanspeur.com")
FULFILMENT_SENDER = DEFAULT_FROM_EMAIL
SITE_BASE_URL = "http://127.0.0.1:8000"
CONTACT_INBOX_EMAIL = os.environ.get("CONTACT_INBOX_EMAIL", "contact@auditsanspeur.com")
RECEIPTS_INBOX_EMAIL = os.environ.get("RECEIPTS_INBOX_EMAIL", "receipts@auditsanspeur.com")
UPLOAD_MAX_BYTES = int(os.environ.get("UPLOAD_MAX_BYTES", "5242880"))

# Charge le fichier .env à la racine du projet en DEV
BASE_DIR_DEV = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR_DEV / '.env')


# === AUTOCONFIG: DOTENV (project .env) ===
import os
from pathlib import Path
try:
    from dotenv import load_dotenv  # type: ignore
    # dev.py est dans config/settings → le dossier projet (avec manage.py et .env) est parents[1]
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    load_dotenv(PROJECT_DIR / ".env")
except Exception:
    pass

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "contact@auditsanspeur.com")

# Compatibilité: si BONUS_DESTINATION_EMAIL est défini, il domine CONTACT_INBOX_EMAIL
CONTACT_INBOX_EMAIL = os.environ.get("BONUS_DESTINATION_EMAIL",
                        os.environ.get("CONTACT_INBOX_EMAIL", "contact@auditsanspeur.com"))

RECEIPTS_INBOX_EMAIL = os.environ.get("RECEIPTS_INBOX_EMAIL", "receipts@auditsanspeur.com")
UPLOAD_MAX_BYTES = int(os.environ.get("UPLOAD_MAX_BYTES", "5242880"))

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Configuration Celery pour développement sans Redis
# SOLUTION RECOMMANDÉE : Exécution synchrone (pas besoin de worker ni Redis)
CELERY_TASK_ALWAYS_EAGER = True  # Exécute les tâches immédiatement
CELERY_TASK_EAGER_PROPAGATES = True

# Alternative 1: Utiliser la base de données Django comme broker
# (Décommentez si vous préférez un worker asynchrone)
# PRÉREQUIS: pip install "kombu[db]"
# CELERY_BROKER_URL = "db+postgresql://{}:{}@{}:{}/{}".format(
#     DATABASES['default']['USER'],
#     DATABASES['default']['PASSWORD'],
#     DATABASES['default']['HOST'],
#     DATABASES['default']['PORT'],
#     DATABASES['default']['NAME']
# )
# CELERY_RESULT_BACKEND = "db+postgresql://{}:{}@{}:{}/{}".format(
#     DATABASES['default']['USER'],
#     DATABASES['default']['PASSWORD'],
#     DATABASES['default']['HOST'],
#     DATABASES['default']['PORT'],
#     DATABASES['default']['NAME']
# )
# CELERY_TASK_ALWAYS_EAGER = False

# Alternative 2: Utiliser Redis (si installé)
# CELERY_BROKER_URL = "redis://localhost:6379/0"
# CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
# CELERY_TASK_ALWAYS_EAGER = False


# === AUTOCONFIG: IMAP RECEIPTS → settings ===
# Expose les variables IMAP au namespace Django settings (utilisées par fetch_receipts)
RECEIPTS_IMAP_HOST = os.environ.get("RECEIPTS_IMAP_HOST")
RECEIPTS_IMAP_PORT = int(os.environ.get("RECEIPTS_IMAP_PORT", "993"))
RECEIPTS_IMAP_SSL  = str(os.environ.get("RECEIPTS_IMAP_SSL", "true")).lower() in ("1", "true", "yes")
RECEIPTS_IMAP_USER = os.environ.get("RECEIPTS_IMAP_USER")
RECEIPTS_IMAP_PASSWORD = os.environ.get("RECEIPTS_IMAP_PASSWORD")
RECEIPTS_IMAP_FOLDER = os.environ.get("RECEIPTS_IMAP_FOLDER", "INBOX")

