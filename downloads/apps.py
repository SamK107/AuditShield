from django.apps import AppConfig


class DownloadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "downloads"

    def ready(self):
        from . import signals  # noqa

