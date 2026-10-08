from django.contrib import admin
from django.urls import include, path, re_path

from config.spa import spa

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    # SPA fallback: WhiteNoise serves real files from frontend/dist first;
    # anything else (client routes) gets index.html.
    # Exclude api/ and admin/ so APPEND_SLASH can redirect /admin → /admin/.
    re_path(r"^(?!(?:api|admin)(?:/|$)).*$", spa, name="spa"),
]
