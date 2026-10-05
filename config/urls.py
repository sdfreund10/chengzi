from django.contrib import admin
from django.urls import include, path, re_path

from config.spa import spa

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    # SPA fallback: WhiteNoise serves real files from frontend/dist first;
    # anything else (client routes) gets index.html.
    re_path(r"^(?!api(?:/|$)).*$", spa, name="spa"),
]
