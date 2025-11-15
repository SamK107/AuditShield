# Import Celery pour qu'il soit chargé au démarrage de Django (tolérant si absent)
try:
    from .celery import app as celery_app  # type: ignore
except Exception:
    celery_app = None  # Celery non installé en dev/local pour certaines commandes

__all__ = ("celery_app",)

