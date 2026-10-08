from django.test import Client


def test_admin_without_trailing_slash_redirects_to_admin() -> None:
    client = Client()
    response = client.get("/admin", follow=False)

    assert response.status_code == 301
    assert response.headers["Location"] == "/admin/"


def test_admin_login_is_django_admin_not_spa() -> None:
    client = Client()
    response = client.get("/admin/login/", follow=False)

    assert response.status_code == 200
    body = response.content.decode()
    assert "Django administration" in body
    assert "Session login for your study account" not in body
