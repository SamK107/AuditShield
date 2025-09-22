import pytest
from downloads.models import DownloadCategory

@pytest.fixture
def cat_checklists(db):
    return DownloadCategory.objects.create(
        slug="checklists", title="Checklists", page_path="/checklists", is_protected=False
    )

@pytest.fixture
def cat_bonus(db):
    return DownloadCategory.objects.create(
        slug="bonus", title="Bonus", page_path="/bonus", is_protected=True, required_sku="EBOOK_ASP"
    )
