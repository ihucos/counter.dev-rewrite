import hmac

from django.conf import settings
from rest_framework import authentication, exceptions


class IngressSecretAuthentication(authentication.BaseAuthentication):
    """Authenticate the ingress endpoint via a shared secret header."""

    keyword = "Bearer"
    header = "HTTP_X_INGRESS_SECRET"

    def authenticate(self, request):
        provided = request.META.get(self.header)
        if not provided:
            # Allow Authorization: Bearer <secret> as an alternative
            auth = request.META.get("HTTP_AUTHORIZATION", "")
            if auth.startswith(self.keyword + " "):
                provided = auth[len(self.keyword) + 1 :]
        if not provided:
            return None
        if not hmac.compare_digest(provided, settings.INGRESS_SECRET_KEY):
            raise exceptions.AuthenticationFailed("Invalid ingress secret.")
        return (IngressClient(), None)


class IngressClient:
    """Anonymous principal representing the ingress secret-key holder."""

    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __str__(self) -> str:
        return "ingress"
