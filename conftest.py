import pytest


@pytest.fixture(autouse=True)
def _safe_email_backend(settings):
    # Prevent real emails during tests
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    return settings
