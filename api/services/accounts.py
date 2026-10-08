from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def normalize_login_email(value: str) -> str:
    """Lowercase login identifier so unique username matches case-insensitive sign-in."""
    return value.strip().lower()


def apply_login_email(user: User, email: str) -> str:
    """Require an email-shaped login id and write it to both username and email."""
    email = normalize_login_email(email)
    try:
        validate_email(email)
    except ValidationError as exc:
        raise ValidationError(exc.messages) from exc
    user.username = email
    user.email = email
    return email
