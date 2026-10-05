from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Note
from .serializers import NoteSerializer


@api_view(["GET"])
def health(request: Request) -> Response:
    return Response(
        {
            "status": "ok",
            "service": "chengzi",
            "database": "connected",
        }
    )


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
