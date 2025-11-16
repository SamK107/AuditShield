"""
Configuration Django pour l'environnement de production
"""
from .base import *  # noqa: F403, F401
import os

# Mode production
DEBUG = False

# Récupérer les hosts depuis l'environnement
ALLOWED_HOSTS = env.list(  # noqa: F405
    'ALLOWED_HOSTS',
    [
        'auditsanspeur.com',
        'www.auditsanspeur.com',
        'web51.lws-hosting.com',
        '127.0.0.1',
        'localhost',
    ]
)

# CSRF Trusted Origins pour la production
CSRF_TRUSTED_ORIGINS = env.list(  # noqa: F405
    'CSRF_TRUSTED_ORIGINS',
    ['https://auditsanspeur.com', 'https://www.auditsanspeur.com'],
)

# Base de données PostgreSQL pour la production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('DB_NAME'),  # noqa: F405
        'USER': env.str('DB_USER'),  # noqa: F405
        'PASSWORD': env.str('DB_PASSWORD'),  # noqa: F405
        'HOST': env.str('DB_HOST', '127.0.0.1'),  # noqa: F405
        'PORT': env.int('DB_PORT', 5432),  # noqa: F405
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', 60),  # noqa: F405
    }
}

# Templates pour la production (sans debug context processor)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # noqa: F405
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Sécurité renforcée en production
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# HSTS (HTTP Strict Transport Security)
# 1 jour pour commencer
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', 86400)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(  # noqa: F405
    'SECURE_HSTS_INCLUDE_SUBDOMAINS', False
)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', False)  # noqa: F405

# Derrière proxy/CDN (LWS/Varnish)
if env.bool('USE_SECURE_PROXY_SSL_HEADER', True):  # noqa: F405
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Logging en production
LOG_DIR = BASE_DIR / 'logs'  # noqa: F405
os.makedirs(LOG_DIR, exist_ok=True)

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
        'app_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'app.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['app_file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['app_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# -----------------------------------------------------------------------------
# Email - Production
# -----------------------------------------------------------------------------
# Utilise votre serveur SMTP auditsanspeur.com en SSL sur le port 465.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.str('EMAIL_HOST', 'auditsanspeur.com')  # noqa: F405
EMAIL_PORT = env.int('EMAIL_PORT', 465)  # noqa: F405
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', True)  # noqa: F405
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', False)  # noqa: F405
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'contact@auditsanspeur.com')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')  # noqa: F405
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', 20)  # noqa: F405

DEFAULT_FROM_EMAIL = env.str(  # noqa: F405
    'DEFAULT_FROM_EMAIL',
    'Audit Sans Peur <contact@auditsanspeur.com>',
)
FULFILMENT_SENDER = os.getenv('FULFILMENT_SENDER', DEFAULT_FROM_EMAIL)
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

# Domaine public utilisé pour construire les URLs absolues dans les emails
SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'https://www.auditsanspeur.com')

# -----------------------------------------------------------------------------
# Paiements - Production (désactive tout mock, URLs publiques)
# -----------------------------------------------------------------------------
# Sécurité: forcer la désactivation du mode mock en production
CINETPAY_MOCK = False

# URLs CinetPay (fallbacks prod si non fournis en env)
CINETPAY_NOTIFY_URL = os.getenv(
    "CINETPAY_NOTIFY_URL",
    f"{SITE_BASE_URL}/payments/cinetpay/notify/",
)
CINETPAY_RETURN_URL = os.getenv(
    "CINETPAY_RETURN_URL",
    f"{SITE_BASE_URL}/payments/cinetpay/return/",
)
CINETPAY_CANCEL_URL = os.getenv(
    "CINETPAY_CANCEL_URL",
    f"{SITE_BASE_URL}/payments/cinetpay/cancel/",
)

# Orange Money: URLs de retour/notification (fallbacks prod)
OM_NOTIFY_URL = os.getenv(
    "OM_NOTIFY_URL",
    f"{SITE_BASE_URL}/payments/om/notify/",
)
OM_RETURN_URL = os.getenv(
    "OM_RETURN_URL",
    f"{SITE_BASE_URL}/payments/om/return/",
)
