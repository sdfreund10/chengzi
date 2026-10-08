from rest_framework import exceptions, status
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """Keep NotAuthenticated as 401 for the SPA.

    DRF coerces 401 → 403 when no WWW-Authenticate header is set (to avoid
    browser basic-auth dialogs). Our JSON client relies on 401 to send users
    back to the login screen.
    """
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        exc.status_code = status.HTTP_401_UNAUTHORIZED
    return drf_exception_handler(exc, context)
