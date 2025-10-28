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
