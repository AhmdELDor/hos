from rest_framework.response import Response


def success_response(data, status=200):
    body = {
        "success": True,
        "data": data,
    }
    return Response(body, status=status)


def error_response(message, status=400, details=None):
    body = {
        "success": False,
        "error": {
            "message": message,
            "details": details,
        },
    }
    return Response(body, status=status)
