from django.urls import path

from .auth_views import login_view, logout_view, me
from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/me/", me, name="auth-me"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
]
