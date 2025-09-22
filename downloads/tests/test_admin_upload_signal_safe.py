import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from downloads.models import DownloadableAsset, DownloadCategory


@pytest.mark.django_db
def test_signal_does_not_crash_when_optional_fields_missing():
    # Prépare une catégorie existante (via seed_download_pages ou création rapide)
    cat, _ = DownloadCategory.objects.get_or_create(
        slug="checklists",
        defaults={"title": "Checklists", "page_path": "/checklists", "order": 1}
    )

    # Fichier factice
    content = b"Hello world"
    upload = SimpleUploadedFile("hello.txt", content, content_type="text/plain")

    # Création d'un asset sans slug => le signal doit générer le slug et NE PAS planter
    a = DownloadableAsset.objects.create(
        category=cat,
        title="Hello",
        short_desc="Test",
        file=upload,
        is_published=True,
        order=0,
    )

    assert a.slug  # slug auto
    assert a.file.name.endswith(".txt")
