from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from api.services.health import check_db_health


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    db_health = check_db_health()
    if db_health:
        return Response(
            {
                "status": "ok",
                "service": "juzi",
                "database": "connected",
            },
            status=HTTP_200_OK,
        )
    else:
        return Response(
            {
                "status": "error",
                "service": "juzi",
                "database": "disconnected",
            },
            status=HTTP_500_INTERNAL_SERVER_ERROR,
        )
