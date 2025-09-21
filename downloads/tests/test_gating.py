import pytest
from django.urls import reverse

from downloads.models import DownloadCategory, DownloadEntitlement


@pytest.mark.django_db
def test_public_category_accessible(client):
    cat = DownloadCategory.objects.get(slug="checklists")
    assert not cat.is_protected
    r = client.get(cat.get_absolute_url())
    assert r.status_code == 200

@pytest.mark.django_db
def test_protected_category_redirects(client):
    cat = DownloadCategory.objects.get(slug="bonus")
    cat.is_protected = True
    cat.save()
    r = client.get(cat.get_absolute_url(), follow=False)
    assert r.status_code in (301, 302)
    assert reverse("downloads_public:claim_access") in r.headers.get("Location", "")

@pytest.mark.django_db
def test_entitlement_allows_access(client):
    cat = DownloadCategory.objects.get(slug="bonus")
    cat.is_protected = True
    cat.save()
    # simule un email validé en session
    s = client.session
    s["verified_email"] = "test@example.com"
    s.save()
    DownloadEntitlement.objects.get_or_create(email="test@example.com", category=cat)
    r = client.get(cat.get_absolute_url())
    assert r.status_code == 200
    assert r.headers.get("X-Robots-Tag") == "noindex, nofollow"
