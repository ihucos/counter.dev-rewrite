"""DRF authentication: session auth extended with guest/share and demo access."""
from rest_framework.authentication import SessionAuthentication

from .accounts import _resolve_account


class AccountAuthentication(SessionAuthentication):
    """Session auth, extended with guest/share and demo access.

    Extends SessionAuthentication with the ?user=<uuid>&token=<token> and
    ?demo=1 fallbacks. A non-None authenticate_header makes DRF answer
    NotAuthenticated with 401 instead of 403, which the SPA treats as
    "not signed in".
    """

    WWW_AUTHENTICATE_HEADER = "Session"

    def authenticate(self, request):
        user, sessionless, demo = _resolve_account(request._request)
        request.sessionless = sessionless
        request.demo = demo
        if user is None:
            return None
        # CSRF is deliberately not enforced: the API is CSRF-exempt by design
        # (see the CORS note in settings) and relies on the SameSite session
        # cookie alone.
        return (user, None)

    def authenticate_header(self, request):
        return self.WWW_AUTHENTICATE_HEADER