import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory

User = get_user_model()


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(
        username="alice@example.com",
        email="alice@example.com",
        password="s3cret-alice",
    )


@pytest.fixture
def other_user(db) -> User:
    return User.objects.create_user(
        username="bob@example.com",
        email="bob@example.com",
        password="s3cret-bob",
    )


@pytest.fixture
def client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


def _csrf_headers(client: APIClient) -> dict[str, str]:
    response = client.get(reverse("auth-me"))
    assert response.status_code == status.HTTP_200_OK
    token = client.cookies["csrftoken"].value
    return {"HTTP_X_CSRFTOKEN": token}


@pytest.mark.django_db
def test_me_anonymous_sets_csrf_cookie(client: APIClient) -> None:
    response = client.get(reverse("auth-me"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"authenticated": False, "email": None}
    assert "csrftoken" in client.cookies


@pytest.mark.django_db
def test_login_rejects_bad_credentials_without_field_hints(client: APIClient, user: User) -> None:
    headers = _csrf_headers(client)
    response = client.post(
        reverse("auth-login"),
        {"email": "alice@example.com", "password": "wrong"},
        format="json",
        **headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body == {"detail": "Invalid email or password."}
    assert "email" not in body
    assert "password" not in body


@pytest.mark.django_db
def test_login_is_case_insensitive_for_email(client: APIClient, user: User) -> None:
    headers = _csrf_headers(client)
    response = client.post(
        reverse("auth-login"),
        {"email": "Alice@Example.com", "password": "s3cret-alice"},
        format="json",
        **headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"authenticated": True, "email": "alice@example.com"}


@pytest.mark.django_db
def test_login_logout_and_me_roundtrip(client: APIClient, user: User) -> None:
    headers = _csrf_headers(client)

    login_response = client.post(
        reverse("auth-login"),
        {"email": "alice@example.com", "password": "s3cret-alice"},
        format="json",
        **headers,
    )
    assert login_response.status_code == status.HTTP_200_OK
    assert login_response.json() == {"authenticated": True, "email": "alice@example.com"}

    me_response = client.get(reverse("auth-me"))
    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.json() == {"authenticated": True, "email": "alice@example.com"}

    # Session auth re-enforces CSRF once logged in.
    headers = _csrf_headers(client)
    logout_response = client.post(reverse("auth-logout"), format="json", **headers)
    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {"authenticated": False, "email": None}

    me_after = client.get(reverse("auth-me"))
    assert me_after.json() == {"authenticated": False, "email": None}


@pytest.mark.django_db
def test_logout_requires_authentication(client: APIClient) -> None:
    headers = _csrf_headers(client)
    response = client.post(reverse("auth-logout"), format="json", **headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_default_permission_rejects_anonymous() -> None:
    """Future study endpoints inherit IsAuthenticated and must reject anonymous callers."""

    @api_view(["GET"])
    def probe(request):
        return Response({"ok": True})

    factory = APIRequestFactory()
    request = factory.get("/probe/")
    response = probe(request)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_userword_rows_are_scoped_per_user(user: User, other_user: User) -> None:
    from api.models import UserWord, Word

    word = Word.objects.create(chinese="字", pinyin="zì", english_basic="character")
    UserWord.objects.create(user=user, word=word, mode=UserWord.Mode.ZH_TO_EN)
    UserWord.objects.create(user=other_user, word=word, mode=UserWord.Mode.ZH_TO_EN)

    assert UserWord.objects.filter(user=user).count() == 1
    assert UserWord.objects.filter(user=other_user).count() == 1
    assert UserWord.objects.filter(user=user).get().user_id == user.id
