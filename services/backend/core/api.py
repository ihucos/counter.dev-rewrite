"""Readonly DRF API for the sites resource (the Host model).

Authentication mirrors the dashboard-data endpoints: session cookie, guest
share access via ?user=<uuid>&token=<token>, or read-only demo access via
?demo=1. Requests resolving to no account get a 401, which the SPA treats
as "not signed in".
"""
from rest_framework import permissions
from rest_framework.exceptions import NotFound, NotAuthenticated
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Host
from .views import _resolve_account, _sites_for
# The plain JSON views (login, query, me, ...) live in core.views; re-export
# them here so urls.py can address both under `core.api`.
from .views import (  # noqa: F401
    account_edit_view,
    delete_site_view,
    delete_token_view,
    delete_user_view,
    feedback_view,
    lang_view,
    login_view,
    logout_view,
    me_view,
    newsletter_register_view,
    query_view,
    recover_view,
    register_view,
    reset_token_view,
    set_pref_range_view,
    set_pref_site_view,
    subscribed_view,
)


class AccountAuthentication:
    """Resolve the request to an account or raise 401."""

    # A non-None header makes DRF answer NotAuthenticated with 401 instead
    # of falling back to 403.
    WWW_AUTHENTICATE_HEADER = "Session"

    def authenticate(self, request):
        # Resolve against the underlying Django request: touching DRF's lazy
        # request.user here would recurse back into authenticate().
        user, sessionless, demo = _resolve_account(request._request)
        request.sessionless = sessionless
        request.demo = demo
        if user is None:
            raise NotAuthenticated()
        return (user, None)

    def authenticate_header(self, request):
        return self.WWW_AUTHENTICATE_HEADER


class HostSerializer(ModelSerializer):
    class Meta:
        model = Host
        fields = ["name", "hide"]


class SiteViewSet(ReadOnlyModelViewSet):
    """List/retrieve only: the sites a user has, in name order.

    The list response is the source of truth for which sites an account
    has (setup-vs-dashboard routing and the site selector).
    """

    serializer_class = HostSerializer
    authentication_classes = [AccountAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return _sites_for(_resolve_account(self.request._request)[0])

    def get_object(self):
        # Sites are unique per user, not globally, so look the name up
        # within the account's own queryset.
        obj = self.get_queryset().filter(name=self.kwargs["site"]).first()
        if obj is None:
            raise NotFound()
        return obj