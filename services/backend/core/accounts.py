"""Account resolution for dashboard access.

Resolves which account a request acts on: the session user, then guest/share
access via ?user=<uuid>&token=<token>, then demo access via ?demo=1 (the
seeded "demo" account, read-only).
"""
import secrets

from django.contrib.auth import get_user_model

from .models import Host

User = get_user_model()


def _guest_user(request):
    """Resolve guest/share access from ?user=<uuid>&token=<token>."""
    uuid_or_name = request.GET.get("user")
    token = request.GET.get("token")
    if not uuid_or_name or not token:
        return None
    try:
        account = User.objects.get(uuid=uuid_or_name)
    except (User.DoesNotExist, ValueError):
        return None
    if not account.share_token or not secrets.compare_digest(account.share_token, token):
        return None
    return account


def _demo_user(request):
    """Resolve demo access (?demo=1) to the seeded "demo" account, if any."""
    if request.GET.get("demo") not in ("1", "true"):
        return None
    return User.objects.filter(username="demo").first()


def _resolve_account(request):
    """Resolve the account a request acts on.

    Returns (user, sessionless, demo); user is None when nothing matched.
    """
    if request.user.is_authenticated:
        return request.user, False, False
    user = _guest_user(request)
    if user is not None:
        return user, True, False
    user = _demo_user(request)
    if user is not None:
        return user, True, True
    return None, False, False


def _sites_for(user):
    hosts = Host.objects.filter(user=user)
    if user.hide_hosts:
        hosts = hosts.filter(hide=False)
    return hosts.order_by("name")