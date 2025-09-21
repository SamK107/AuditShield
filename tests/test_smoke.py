import pytest


@pytest.mark.django_db
def test_admin_login_page(client):
    resp = client.get("/admin/login/")
    assert resp.status_code in (200, 302)

@pytest.mark.parametrize("path", ["/", "/offres/"])
@pytest.mark.django_db
def test_core_pages_do_not_500(client, path):
    resp = client.get(path)
    # Accept 200/301/302/404 as long as it's not a 500
    assert resp.status_code in (200, 301, 302, 404)

@pytest.mark.django_db
def test_download_route_exists(client):
    # Unknown slug: route should not 500
    resp = client.get("/downloads/test-slug/")
    assert resp.status_code in (200, 301, 302, 404)
