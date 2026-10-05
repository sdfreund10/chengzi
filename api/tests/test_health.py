import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoint() -> None:
    client = APIClient()
    response = client.get(reverse("health"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "ok",
        "service": "chengzi",
        "database": "connected",
    }
