from django.conf import settings
from django.http import HttpResponse


class CorsMiddleware:
    """Cross-origin API access: the SPA is served from counter.dev and calls
    api.counter.dev directly. Adds CORS headers to API responses and answers
    preflights, with credentials so the session cookie flows."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        allowed = origin in settings.CORS_ALLOWED_ORIGINS
        if request.method == "OPTIONS" and allowed:
            response = HttpResponse()
        else:
            response = self.get_response(request)
        if allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Vary"] = "Origin"
        if request.method == "OPTIONS" and allowed:
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response