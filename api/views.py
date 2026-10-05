from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from api.services.health import check_db_health


@api_view(["GET"])
def health(request: Request) -> Response:
    db_health = check_db_health()
    if db_health:
        return Response(
            {
                "status": "ok",
                "service": "chengzi",
                "database": "connected",
            },
            status=HTTP_200_OK,
        )
    else:
        return Response(
            {
                "status": "error",
                "service": "chengzi",
                "database": "disconnected",
            },
            status=HTTP_500_INTERNAL_SERVER_ERROR,
        )
