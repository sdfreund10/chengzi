from django.contrib.auth import authenticate, get_user_model, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import LoginSerializer

User = get_user_model()

INVALID_CREDENTIALS = {"detail": "Invalid email or password."}


def _user_payload(user) -> dict:
    return {
        "authenticated": True,
        "email": user.email,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def me(request: Request) -> Response:
    """Return the current session user, and ensure the CSRF cookie is set."""
    if request.user.is_authenticated:
        return Response(_user_payload(request.user))
    return Response({"authenticated": False, "email": None})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request: Request) -> Response:
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"].strip()
    password = serializer.validated_data["password"]

    # Built-in auth still keys off username; we look up by email, then authenticate.
    try:
        account = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response(INVALID_CREDENTIALS, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=account.get_username(), password=password)
    if user is None:
        return Response(INVALID_CREDENTIALS, status=status.HTTP_400_BAD_REQUEST)

    login(request, user)
    return Response(_user_payload(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request: Request) -> Response:
    logout(request)
    return Response({"authenticated": False, "email": None})
