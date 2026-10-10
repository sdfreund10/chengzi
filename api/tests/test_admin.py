import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.mark.django_db
def test_admin_user_add_page_renders() -> None:
    admin = User.objects.create_superuser(
        "admin@test.com",
        "admin@test.com",
        "local-test-password",
    )
    client = Client()
    client.force_login(admin)

    response = client.get("/admin/auth/user/add/")

    assert response.status_code == 200
    body = response.content.decode()
    assert "Password-based authentication" in body
