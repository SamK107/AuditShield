import pytest


@pytest.fixture(autouse=True)
def _safe_email_backend(settings, monkeypatch):
    # Prevent real emails & make statics simple while testing
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    monkeypatch.setenv("USE_WHITENOISE", "0")
    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    return settings


@pytest.fixture
def seed_download_categories(db):
    from downloads.models import DownloadCategory

    checklists, _ = DownloadCategory.objects.get_or_create(
        slug="checklists",
        defaults=dict(
            title="Checklists",
            page_path="/checklists",
            subtitle="—",
            description="—",
            order=1,
            is_protected=False,
            required_sku="",
        ),
    )
    bonus, _ = DownloadCategory.objects.get_or_create(
        slug="bonus",
        defaults=dict(
            title="Bonus",
            page_path="/bonus",
            subtitle="—",
            description="—",
            order=2,
            is_protected=True,
            required_sku="EBOOK_ASP",
        ),
    )
    return {"checklists": checklists, "bonus": bonus}
