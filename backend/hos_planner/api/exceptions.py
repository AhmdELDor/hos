import logging

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

from hos_planner.api.responses import error_response

logger = logging.getLogger(__name__)


class MapServiceError(APIException):
    status_code = 502
    default_detail = "The map service is not available right now. Please try again later."
    default_code = "map_service_error"


class RouteNotFoundError(APIException):
    status_code = 422
    default_detail = "No driving route was found between these locations."
    default_code = "route_not_found"


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unexpected error", exc_info=exc)
        return error_response("Something went wrong on the server.", status=500)

    if isinstance(exc, ValidationError):
        return error_response("The input is not valid.", response.status_code, response.data)

    return error_response(response.data["detail"], response.status_code)
