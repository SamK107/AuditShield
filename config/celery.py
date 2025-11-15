"""
Configuration Celery pour le projet
"""
import os
from celery import Celery

# Définir le module de settings par défaut
# Le namespace CELERY cherchera automatiquement CELERY_BROKER_URL dans les settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("auditshield")

# Charger la configuration depuis les settings Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Découvrir automatiquement les tâches dans les apps Django
app.autodiscover_tasks()

