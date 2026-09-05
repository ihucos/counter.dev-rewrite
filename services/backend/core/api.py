"""Vanilla DRF API for the counter.dev backend.

Authentication resolves to an account three ways: session cookie (SPA),
guest/share access via ?user=<uuid>&token=<token>, or read-only demo access
via ?demo=1. Requests resolving to no account get a 401, which the SPA
treats as "not signed in".
"""
import secrets
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from rest_framework import permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ReadOnlyModelViewSet
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from .accounts import _sites_for
from .authentication import AccountAuthentication
from .models import Count, Host
from .serializers import (
    AccountEditSerializer,
    FeedbackSerializer,
    LoginSerializer,
    NewsletterSerializer,
    RecoverSerializer,
    RegisterSerializer,
    SubscribedSerializer,
)

User = get_user_model()


class OkResponseSerializer(Serializer):
    """Generic {"ok": true} response body."""

    ok = serializers.BooleanField()


class UserStateSerializer(Serializer):
    id = serializers.CharField()
    uuid = serializers.CharField(allow_blank=True)
    token = serializers.CharField(allow_blank=True)
    prefs = serializers.JSONField()
    timezone = serializers.IntegerField()


class MeMetaSerializer(Serializer):
    utcoffset = serializers.IntegerField()
    sessionless = serializers.BooleanField()
    demo = serializers.BooleanField()


class MeResponseSerializer(Serializer):
    """Body of the /me response: user record and session meta."""

    user = UserStateSerializer()
    meta = MeMetaSerializer()


class LogEntrySerializer(Serializer):
    site = serializers.CharField()
    timestamp = serializers.CharField()
    date = serializers.CharField()
    time = serializers.CharField()
    country = serializers.CharField()
    referrer = serializers.CharField()
    device = serializers.CharField()
    platform = serializers.CharField()
    extra = serializers.CharField()


class QueryResponseSerializer(Serializer):
    """Body of the /query response: per-category visit aggregates plus the
    recent-visits log."""

    site = serializers.CharField()
    start = serializers.DateField()
    end = serializers.DateField()
    visits = serializers.DictField(
        child=serializers.DictField(child=serializers.IntegerField()),
    )
    logs = LogEntrySerializer(many=True)


class TokenResponseSerializer(Serializer):
    token = serializers.CharField()

RANGES = ["day", "yesterday", "last7", "last30", "month", "year", "all"]

# The categories the tracker buckets visits into. The dashboard's components
# read these dimensions unconditionally, so every range bucket sent to the
# frontend must contain them (empty if there is no data yet).
CATEGORIES = [
    "lang",
    "ref",
    "page",
    "date",
    "weekday",
    "platform",
    "browser",
    "device",
    "country",
    "screen",
    "hour",
]


def _utcoffset(request):
    try:
        return int(request.GET.get("utcoffset", "0"))
    except (ValueError, TypeError):
        return 0


def _local_date(utcoffset_hours):
    """Today's date in the viewer's timezone, from a UTC offset in hours.

    The tracker and the frontend both treat utcoffset as whole hours (the
    tracking script embeds e.g. data-utcoffset="2"); stay consistent with
    them and clamp like the tracker does.
    """
    utcoffset_hours = max(-12, min(14, utcoffset_hours))
    return (timezone.now() + timedelta(hours=utcoffset_hours)).date()


def _normalize_domain(value):
    for prefix in ["https://", "http://", "www."]:
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.rstrip("/")


def _query_site_data(host: Host, start: date, end: date) -> dict[str, dict[str, int]]:
    """Query aggregated data for a single host within a date range."""
    qs = Count.objects.filter(host=host, date__gte=start, date__lte=end)
    result: dict[str, dict[str, int]] = defaultdict(dict)
    rows = qs.values("category", "item").annotate(total=Sum("total"))
    for row in rows:
        result[row["category"]][row["item"]] = row["total"]
    return dict(result)


def parse_log_line(line):
    """
    Parse a log line from the tracker.

    Format: [YYYY-MM-DD HH:MM:SS] <country> <referrer_url> <device> <platform>

    Returns a dict with parsed fields or None if parsing fails.
    """
    try:
        if not line.startswith("["):
            return None
        bracket_end = line.index("]")
        timestamp = line[1:bracket_end].strip()
        rest = line[bracket_end + 1:].strip()
    except (ValueError, IndexError):
        return None

    parts = rest.split()
    if len(parts) < 3:
        return None

    country = parts[0] if parts[0] != "-" else ""
    referrer = parts[1] if len(parts) > 1 and parts[1] != "-" else ""
    device = parts[2] if len(parts) > 2 else ""
    platform = parts[3] if len(parts) > 3 else ""
    extra = " ".join(parts[4:]) if len(parts) > 4 else ""

    try:
        ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        date_str = ts.strftime("%Y-%m-%d")
        time_str = ts.strftime("%H:%M:%S")
    except ValueError:
        date_str = timestamp[:10] if len(timestamp) >= 10 else ""
        time_str = timestamp[11:19] if len(timestamp) >= 19 else ""

    return {
        "timestamp": timestamp,
        "date": date_str,
        "time": time_str,
        "country": country.lower() if country else "",
        "referrer": referrer,
        "device": device,
        "platform": platform,
        "extra": extra,
    }


def _get_user_logs(user, site: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    """Fetch recent visit logs from Redis for the user's sites."""
    try:
        redis = cache._cache.get_client()
    except Exception:
        return []

    hosts = Host.objects.filter(user=user)
    if site:
        hosts = hosts.filter(name=site)

    logs: list[dict[str, Any]] = []
    for host in hosts:
        log_key = f"log:{host.name}:{user.username}"
        try:
            entries = redis.zrevrange(log_key, 0, limit - 1, withscores=True)
        except Exception:
            continue

        for entry_bytes, _ in entries:
            try:
                log_line = entry_bytes.decode("utf-8", errors="replace")
            except Exception:
                continue
            log_entry = parse_log_line(log_line)
            if log_entry:
                log_entry["site"] = host.name
                logs.append(log_entry)

    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return logs[:limit]


@extend_schema(request=LoginSerializer, responses=OkResponseSerializer, auth=None)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        request._request,
        username=serializer.validated_data["user"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        if not User.objects.filter(username=serializer.validated_data["user"]).exists():
            raise ValidationError({"detail": "no such user"})
        raise ValidationError({"detail": "wrong password"})
    login(request._request, user)
    return Response({"ok": True})


@extend_schema(responses={302: None}, auth=None)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def logout_view(request):
    """End the session. Reached via the navbar's plain "Sign out" link, so
    accept GET and send the browser back to the SPA it came from."""
    if request.user.is_authenticated:
        logout(request._request)
    referer = request.headers.get("referer", "")
    try:
        parts = urlparse(referer)
        origin = f"{parts.scheme}://{parts.netloc}" if parts.netloc else ""
    except ValueError:
        origin = ""
    return redirect(f"{origin or 'https://counter.dev'}/welcome.html")


@extend_schema(request=RegisterSerializer, responses=OkResponseSerializer, auth=None)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if User.objects.filter(username=data["user"]).exists():
        raise ValidationError({"detail": "user already exists"})
    account = User.objects.create_user(username=data["user"], email=data["mail"], password=data["password"])
    account.timezone = data["utcoffset"]
    account.save(update_fields=["timezone"])
    login(request._request, account)
    return Response({"ok": True})


@extend_schema(request=RecoverSerializer, responses=OkResponseSerializer, auth=None)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def recover_view(request):
    serializer = RecoverSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    account = User.objects.filter(
        username=serializer.validated_data["user"], email=serializer.validated_data["mail"]
    ).first()
    if account is not None:
        send_mail(
            "counter.dev account recovery",
            f"Recovery was requested for the account {account.username}.\n"
            f"If this was you, sign in at {settings.PASSWORD_RESET_URL_BASE} "
            "to reset your password.",
            settings.DEFAULT_FROM_EMAIL,
            [serializer.validated_data["mail"]],
            fail_silently=True,
        )
    return Response({"ok": True})


@extend_schema(request=AccountEditSerializer, responses=OkResponseSerializer)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def account_edit_view(request):
    serializer = AccountEditSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    user = request.user

    user.timezone = data["utcoffset"]
    user.email = data["mail"]
    prefs = dict(user.prefs or {})
    prefs["usesites"] = data["usesites"]
    user.prefs = prefs

    names = [_normalize_domain(s.strip()) for s in data["sites"].splitlines() if s.strip()]
    existing = {h.name: h for h in Host.objects.filter(user=user)}
    for name in names:
        if name not in existing:
            Host.objects.create(user=user, name=name)
    for name, host in existing.items():
        if name not in names:
            host.delete()

    user.save()
    return Response({"ok": True})


@extend_schema(request=None, responses=OkResponseSerializer)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def delete_user_view(request):
    request.user.delete()
    return Response({"ok": True})


@extend_schema(request=FeedbackSerializer, responses=OkResponseSerializer, auth=None)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def feedback_view(request):
    serializer = FeedbackSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    send_mail(
        "counter.dev feedback",
        f"{serializer.validated_data['feedback']}\n\nReply-to: {serializer.validated_data['contact']}",
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        fail_silently=True,
    )
    return Response({"ok": True})


# --- Sites ---------------------------------------------------------------------


@extend_schema(request=None, responses=OkResponseSerializer)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def delete_site_view(request):
    site = (request.user.prefs or {}).get("site")
    if not site:
        raise ValidationError({"detail": "no site selected"})
    host = Host.objects.filter(user=request.user, name=site).first()
    if host is None:
        raise ValidationError({"detail": "no such site"})
    host.delete()  # cascades to its Count rows
    return Response({"ok": True})


# --- Guest / share access --------------------------------------------------------


@extend_schema(request=None, responses=TokenResponseSerializer)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def reset_token_view(request):
    request.user.share_token = secrets.token_urlsafe(24)
    request.user.save(update_fields=["share_token"])
    return Response({"token": request.user.share_token})


@extend_schema(request=None, responses=OkResponseSerializer)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def delete_token_view(request):
    request.user.share_token = ""
    request.user.save(update_fields=["share_token"])
    return Response({"ok": True})


# --- Dashboard preferences -------------------------------------------------------


@extend_schema(
    # The site name is the raw URL-encoded query string, e.g. /set_pref_site?example.com
    parameters=[OpenApiParameter(name="site", type=str, location=OpenApiParameter.QUERY, required=False)],
    responses=OkResponseSerializer,
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def set_pref_site_view(request):
    # The site name is the raw URL-encoded query string, e.g. /set_pref_site?example.com
    site = request.GET.get("site") or request.META.get("QUERY_STRING", "")
    site = unquote(site).strip()
    prefs = dict(request.user.prefs or {})
    prefs["site"] = site
    request.user.prefs = prefs
    request.user.save(update_fields=["prefs"])
    return Response({"ok": True})


@extend_schema(
    parameters=[OpenApiParameter(name="range", type=str, location=OpenApiParameter.QUERY, enum=RANGES)],
    responses=OkResponseSerializer,
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def set_pref_range_view(request):
    value = request.GET.get("range") or request.META.get("QUERY_STRING", "")
    value = unquote(value).strip()
    if value not in RANGES:
        raise ValidationError({"detail": "invalid range"})
    prefs = dict(request.user.prefs or {})
    prefs["range"] = value
    request.user.prefs = prefs
    request.user.save(update_fields=["prefs"])
    return Response({"ok": True})


# --- Dashboard data ---------------------------------------------------------------


@extend_schema(responses=MeResponseSerializer)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    """The signed-in user's state: user record and session meta.

    Feeds session bootstrap (401 means "not signed in") and the
    share-account panel.
    """
    return Response(
        MeResponseSerializer(
            {
                "user": {
                    "id": request.user.username,
                    "uuid": str(request.user.uuid) if request.user.uuid else "",
                    "token": request.user.share_token,
                    "prefs": request.user.prefs or {},
                    "timezone": request.user.timezone,
                },
                "meta": {
                    "utcoffset": _utcoffset(request),
                    "sessionless": request.sessionless,
                    "demo": request.demo,
                },
            }
        ).data
    )


@extend_schema(
    parameters=[
        OpenApiParameter(name="site", type=str, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name="start", type=str, location=OpenApiParameter.QUERY, description="ISO date (YYYY-MM-DD), inclusive; defaults to the beginning of time"),
        OpenApiParameter(name="end", type=str, location=OpenApiParameter.QUERY, description="ISO date (YYYY-MM-DD), inclusive; defaults to a year ahead of today"),
        OpenApiParameter(name="utcoffset", type=int, location=OpenApiParameter.QUERY, description="Viewer's UTC offset in whole hours, used for the default end date"),
        # Guest/share access: instead of a session cookie, a share URL
        # carries the account uuid plus its share token.
        OpenApiParameter(name="user", type=str, location=OpenApiParameter.QUERY, description="Account uuid for guest/share access"),
        OpenApiParameter(name="token", type=str, location=OpenApiParameter.QUERY, description="Share token for guest/share access"),
        OpenApiParameter(name="demo", type=bool, location=OpenApiParameter.QUERY, description="Read-only demo access to the demo site"),
    ],
    responses=QueryResponseSerializer,
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def query_view(request):
    """Analytics data for one site over an open-ended date range.

    Params: site (required), start and end (ISO dates; either or both may be
    omitted). Returns the Count-model aggregates grouped by the tracker
    categories, plus the recent-visits log from Redis.
    """
    user = request.user

    site = request.GET.get("site", "")
    hosts = {h.name: h for h in _sites_for(user)}
    if site not in hosts:
        raise ValidationError({"detail": "no such site"})

    try:
        start = date.fromisoformat(request.GET["start"]) if request.GET.get("start") else None
        end = date.fromisoformat(request.GET["end"]) if request.GET.get("end") else None
    except ValueError:
        raise ValidationError({"detail": "invalid date"})
    # Open-ended: missing bounds fall back to the same "all" window the
    # dashboard previously used.
    start = start or date(2000, 1, 1)
    end = end or _local_date(_utcoffset(request)) + timedelta(days=365)

    visits = _query_site_data(hosts[site], start, end)
    for category in CATEGORIES:
        visits.setdefault(category, {})
    return Response(
        QueryResponseSerializer(
            {
                "site": site,
                "start": start,
                "end": end,
                "visits": visits,
                "logs": _get_user_logs(user, site=site, limit=30),
            }
        ).data
    )


# --- Misc -------------------------------------------------------------------------


@extend_schema(responses=OpenApiTypes.STR, auth=None)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def lang_view(request):
    """
    Return the viewer's language/country code as plain text (e.g. "RU"),
    derived from the Accept-Language header.
    """
    header = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for part in header.split(","):
        tag = part.split(";")[0].strip()
        if not tag or tag == "*":
            continue
        if "-" in tag:
            return HttpResponse(tag.split("-")[1].upper(), content_type="text/plain")
        return HttpResponse(tag.upper(), content_type="text/plain")
    return HttpResponse("EN", content_type="text/plain")


@extend_schema(request=NewsletterSerializer, responses=OkResponseSerializer, auth=None)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def newsletter_register_view(request):
    serializer = NewsletterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    print(f"newsletter subscription: {serializer.validated_data['mail']}")
    return Response({"ok": True})


@extend_schema(request=SubscribedSerializer, responses=OkResponseSerializer)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def subscribed_view(request):
    """Record a PayPal subscription ID after payment approval."""
    serializer = SubscribedSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not request.user.is_authenticated:
        raise NotAuthenticated()
    prefs = dict(request.user.prefs or {})
    prefs["subscription_id"] = serializer.validated_data["subscription_id"]
    request.user.prefs = prefs
    request.user.save(update_fields=["prefs"])
    return Response({"ok": True})


# --- Sites resource (Host model) ---------------------------------------------------


class HostSerializer(ModelSerializer):
    class Meta:
        model = Host
        fields = ["name", "hide"]


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(name="user", type=str, location=OpenApiParameter.QUERY, description="Account uuid for guest/share access"),
            OpenApiParameter(name="token", type=str, location=OpenApiParameter.QUERY, description="Share token for guest/share access"),
            OpenApiParameter(name="demo", type=bool, location=OpenApiParameter.QUERY, description="Read-only demo access to the demo site"),
        ],
    ),
)
class SiteViewSet(ReadOnlyModelViewSet):
    """List/retrieve only: the sites a user has, in name order.

    The list response is the source of truth for which sites an account
    has (setup-vs-dashboard routing and the site selector). The
    AccountAuthentication above resolves sessions, guest/share access and
    demo access to request.user.
    """

    serializer_class = HostSerializer
    authentication_classes = [AccountAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    # Site names are unique per user, not globally, and contain dots, so the
    # default lookup regex (which excludes dots) is widened.
    lookup_field = "name"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        return _sites_for(self.request.user)