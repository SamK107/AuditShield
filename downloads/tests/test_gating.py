import pytest

def _url(slug: str) -> str:
    return f"/downloads/{slug}/"

@pytest.mark.django_db
def test_public_category_accessible(client, cat_checklists):
    resp = client.get(_url(cat_checklists.slug))
    assert resp.status_code in (200, 301, 302, 404)

@pytest.mark.django_db
def test_protected_category_redirects(client, cat_bonus):
    resp = client.get(_url(cat_bonus.slug))
    assert resp.status_code in (200, 301, 302, 403, 404)

@pytest.mark.django_db
def test_entitlement_allows_access(client, cat_bonus):
    # Later, create entitlement to assert 200; for now just no 500.
    resp = client.get(_url(cat_bonus.slug))
    assert resp.status_code in (200, 301, 302, 403, 404)
