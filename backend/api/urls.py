from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NoteViewSet, health

router = DefaultRouter()
router.register("notes", NoteViewSet, basename="note")

urlpatterns = [
    path("health/", health, name="health"),
    path("", include(router.urls)),
]
