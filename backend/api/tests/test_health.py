from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def test_health_endpoint() -> None:
    client = APIClient()
    response = client.get(reverse("health"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "ok",
        "service": "chengzi",
        "database": "connected",
    }
