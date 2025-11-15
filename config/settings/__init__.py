"""
Package settings - Chargement automatique du .env avec python-dotenv
Ce fichier charge les variables d'environnement avant que base.py, dev.py, prod.py ne soient importés
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Chemin vers la racine du projet (où se trouve .env)
# config/settings/__init__.py est à config/settings/, donc parents[2] = auditshield/
BASE_DIR = Path(__file__).resolve().parents[2]

# Charger le fichier .env à la racine du projet
load_dotenv(BASE_DIR / ".env")

# Variables d'environnement pour Celery, OpenAI et Site URL
# Ces variables sont disponibles via os.getenv() dans tout le projet
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

