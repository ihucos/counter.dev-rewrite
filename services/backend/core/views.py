import json
import secrets
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.parse import unquote

from django.contrib.auth import authenticate, get_user_model, login as auth_login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Min, Sum
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django.conf import settings

from .models import Count, Host
from counter.models import Feedback, NewsletterSubscriber

User = get_user_model()


def error(message: str, status: int = 400) -> HttpResponse:
    return HttpResponse(message, status=status, content_type="text/plain")


@require_GET
def index(request):
    return render(request, "index.html")


@require_GET
def privacy(request):
    return render(request, "privacy.html")


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _query_site_data(host: Host, start: date, end: date) -> dict[str, dict[str, int]]:
    """Query aggregated data for a single host within a date range."""
    qs = Count.objects.filter(host=host, date__gte=start, date__lte=end)
    result: dict[str, dict[str, int]] = defaultdict(dict)
    rows = qs.values("category", "item").annotate(total=Sum("total"))
    for row in rows:
        result[row["category"]][row["item"]] = row["total"]
    return dict(result)

def _get_user_logs(
    user, site: Optional[str] = None, limit: int = 50
) -> list[dict[str, Any]]:
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
        rest = line[bracket_end + 1 :].strip()
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


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def resolve_user(request) -> tuple[Optional[User], bool]:
    """
    Return (user, sessionless) for a request.

    Session-authenticated users take precedence; otherwise guest access is
    granted via ?user=<uuid>&token=<share_token>.
    """
    if request.user.is_authenticated:
        return request.user, False

    user_param = request.GET.get("user") or ""
    token_param = request.GET.get("token") or ""
    if user_param and token_param:
        try:
            user = User.objects.get(uuid=user_param, share_token=token_param)
            return user, True
        except (User.DoesNotExist, ValueError):
            return None, True
    return None, False


def _parse_utcoffset(request) -> int:
    try:
        return int(request.GET.get("utcoffset", "0"))
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Dashboard data
# ---------------------------------------------------------------------------


def _build_dump_payload(user: User, utcoffset: int, sessionless: bool) -> dict[str, Any]:
    hosts = Host.objects.filter(user=user)
    if user.hide_hosts:
        hosts = hosts.filter(hide=False)

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    sites_data: dict[str, dict[str, Any]] = {}
    for host in hosts:
        sites_data[host.name] = {
            "visits": {
                "day": _query_site_data(host, today, today),
                "yesterday": _query_site_data(host, yesterday, yesterday),
                "all": _query_site_data(host, date(2000, 1, 1), today + timedelta(days=365)),
            },
            "logs": _get_user_logs(user, site=host.name, limit=30),
        }

    prefs = dict(user.prefs or {})
    prefs.setdefault("utcoffset", utcoffset)
    return {
        "user": {
            "uuid": str(user.uuid) if user.uuid else "",
            "id": user.username,
            "token": user.share_token or "",
            "isSubscribed": bool(user.subscription_id),
            "prefs": prefs,
        },
        "meta": {
            "utcoffset": utcoffset,
            "sessionless": sessionless,
        },
        "sites": sites_data,
    }


def _build_archive_payload(user: User) -> dict[str, dict[str, dict[str, Any]]]:
    """Archive data the frontend merges into last7/last30: ranges end 2 days ago."""
    today = timezone.localdate()
    hosts = Host.objects.filter(user=user)
    if user.hide_hosts:
        hosts = hosts.filter(hide=False)

    archives: dict[str, dict[str, dict[str, Any]]] = {"-7:-2": {}, "-30:-2": {}}
    for host in hosts:
        archives["-7:-2"][host.name] = _query_site_data(
            host, today - timedelta(days=7), today - timedelta(days=2)
        )
        archives["-30:-2"][host.name] = _query_site_data(
            host, today - timedelta(days=30), today - timedelta(days=2)
        )
    return archives


def _oldest_archive_date(user: User) -> Optional[str]:
    oldest = Count.objects.filter(host__user=user).aggregate(d=Min("date"))["d"]
    return oldest.isoformat() if oldest else None


def _sse(event_type: str, payload: Any) -> str:
    return f"data: {json.dumps({'type': event_type, 'payload': payload})}\n\n"


@require_GET
def dump_sse(request):
    """
    Server-Sent Events endpoint streaming the full account state.

    Each message is `data: {"type": ..., "payload": ...}` on the default SSE
    channel (the frontend listens via EventSource.onmessage). Event types:
    signedin, dump, archive, oldest-archive-date, nouser.

    Auth: session cookie, or guest access via ?user=<uuid>&token=<share_token>.
    Guests (sessionless) receive a single dump and the stream ends.
    """
    user, sessionless = resolve_user(request)
    if user is None:
        return StreamingHttpResponse(
            (_sse("nouser", {}),),
            content_type="text/event-stream",
        )

    utcoffset = _parse_utcoffset(request)

    def event_stream():
        try:
            yield _sse("signedin", {})
            yield _sse(
                "dump", _build_dump_payload(user, utcoffset, sessionless)
            )
            yield _sse("archive", _build_archive_payload(user))
            yield _sse("oldest-archive-date", _oldest_archive_date(user))
        except Exception:
            yield _sse("nouser", {})
            return

        if sessionless:
            return

        interval = 15
        while True:
            time.sleep(interval)
            try:
                yield _sse("dump", _build_dump_payload(user, utcoffset, sessionless))
            except Exception:
                yield _sse("nouser", {})
                return

    response = StreamingHttpResponse(
        streaming_content=event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["X-Accel-Buffering"] = "no"
    return response


@require_GET
def daterange_query(request):
    """
    Aggregated data for all of the user's sites within a custom range.
    Returns {site: {category: {item: total}}}. Supports guest access.
    """
    user, _ = resolve_user(request)
    if user is None:
        return error("Not signed in", 401)

    try:
        start = date.fromisoformat(request.GET.get("from", ""))
        end = date.fromisoformat(request.GET.get("to", ""))
    except ValueError:
        return error("Invalid from/to dates")

    hosts = Host.objects.filter(user=user)
    if user.hide_hosts:
        hosts = hosts.filter(hide=False)

    result: dict[str, dict[str, dict[str, int]]] = {}
    for host in hosts:
        result[host.name] = _query_site_data(host, start, end)
    return JsonResponse(result)


@require_GET
def query(request):
    """Single-site aggregation for the authenticated user (internal API)."""
    if not request.user.is_authenticated:
        return error("Not signed in", 403)

    site = request.GET.get("site", "")
    if not site:
        return error("Missing site parameter")

    try:
        host = Host.objects.get(name=site, user=request.user)
    except Host.DoesNotExist:
        return error("Not found", 404)

    try:
        start = date.fromisoformat(request.GET["start_date"]) if request.GET.get("start_date") else None
        end = date.fromisoformat(request.GET["end_date"]) if request.GET.get("end_date") else None
    except ValueError:
        return error("Invalid start_date/end_date")

    qs = Count.objects.filter(host=host)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    result: dict[str, dict[str, int]] = defaultdict(dict)
    for row in qs.values("category", "item").annotate(total=Sum("total")):
        result[row["category"]][row["item"]] = row["total"]
    return JsonResponse(dict(result))


@require_GET
def visit_logs(request):
    """
    Retrieve recent visit log entries from Redis for sites owned by
    the authenticated user.

    Query params:
        site (optional) - filter logs for a specific hostname
        limit (optional) - max number of log entries to return (default: 30)
    """
    if not request.user.is_authenticated:
        return error("Not signed in", 403)

    site_filter = request.GET.get("site")
    try:
        limit = max(1, min(int(request.GET.get("limit", "30")), 100))
    except (ValueError, TypeError):
        limit = 30

    logs = []
    user = request.user
    hosts = Host.objects.filter(user=user)
    if site_filter:
        hosts = hosts.filter(name=site_filter)

    if not hosts:
        return JsonResponse({"logs": [], "sites_with_logs": []})

    sites_with_logs = []
    for host in hosts:
        log_key = f"log:{host.name}:{user.username}"
        try:
            redis = cache._cache.get_client()
            entries = redis.zrevrange(log_key, 0, limit - 1, withscores=True)
        except Exception:
            entries = []

        if entries:
            sites_with_logs.append(host.name)

        for entry_bytes, score in entries:
            log_line = entry_bytes.decode("utf-8", errors="replace")
            log_entry = parse_log_line(log_line)
            if log_entry:
                log_entry["site"] = host.name
                logs.append(log_entry)

    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    logs = logs[:limit]

    return JsonResponse({"logs": logs, "sites_with_logs": sites_with_logs})


# ---------------------------------------------------------------------------
# Authentication & account
# ---------------------------------------------------------------------------


@csrf_exempt
@require_POST
def login_view(request):
    username = request.POST.get("user", "")
    password = request.POST.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return error("Wrong username or password", 403)
    auth_login(request, user)
    return HttpResponse()


@csrf_exempt
@require_POST
def register_view(request):
    username = request.POST.get("user", "").strip()
    mail = request.POST.get("mail", "").strip()
    password = request.POST.get("password", "")
    try:
        utcoffset = int(request.POST.get("utcoffset", "0"))
    except (ValueError, TypeError):
        utcoffset = 0

    if not username or not password:
        return error("Username and password are required")
    if User.objects.filter(username=username).exists():
        return error("Username is already taken")

    user = User.objects.create_user(
        username=username,
        email=mail,
        password=password,
        timezone=utcoffset,
    )
    user.prefs["utcoffset"] = utcoffset
    user.save()
    auth_login(request, user)
    return HttpResponse()


@csrf_exempt
@require_POST
def recover_view(request):
    mail = request.POST.get("mail", "").strip()
    username = request.POST.get("user", "").strip()

    try:
        user = User.objects.get(username=username, email=mail)
    except User.DoesNotExist:
        return error("No matching account found")

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.PASSWORD_RESET_URL_BASE}?uid={uid}&token={token}"
    send_mail(
        "counter.dev password recovery",
        f"Reset your password: {reset_url}",
        settings.DEFAULT_FROM_EMAIL,
        [mail],
    )
    return HttpResponse()


@csrf_exempt
@require_POST
def account_edit(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    user = request.user

    try:
        utcoffset = int(request.POST.get("utcoffset", "0"))
    except (ValueError, TypeError):
        return error("Invalid utcoffset")

    new_password = request.POST.get("new_password", "")
    if new_password:
        if not user.check_password(request.POST.get("current_password", "")):
            return error("Wrong current password")
        if new_password != request.POST.get("repeat_new_password", ""):
            return error("Passwords do not match")
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return error("; ".join(e.messages))
        user.set_password(new_password)

    user.timezone = utcoffset
    user.email = request.POST.get("mail", "").strip()
    user.prefs["utcoffset"] = utcoffset
    user.prefs["usesites"] = request.POST.get("usesites", "") == "1"
    user.prefs["sites"] = request.POST.get("sites", "")
    user.save()
    return HttpResponse()


@csrf_exempt
@require_POST
def delete_user(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    confirm = request.POST.get("confirmUser", "")
    if confirm and confirm != request.user.username:
        return error("Username does not match")
    request.user.delete()
    return HttpResponse()


@csrf_exempt
@require_POST
def delete_site(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    site = request.user.prefs.get("site", "")
    if not site:
        return error("No site selected")
    deleted, _ = Host.objects.filter(user=request.user, name=site).delete()
    if not deleted:
        return error("Not found", 404)
    return HttpResponse()


@csrf_exempt
@require_POST
def feedback_view(request):
    message = request.POST.get("feedback", "").strip()
    if not message:
        return error("Feedback message is required")
    Feedback.objects.create(
        message=message,
        contact=request.POST.get("contact", "").strip(),
    )
    return HttpResponse()


# ---------------------------------------------------------------------------
# Guest / share access
# ---------------------------------------------------------------------------


@csrf_exempt
@require_POST
def reset_token(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    request.user.share_token = secrets.token_urlsafe(32)
    request.user.save(update_fields=["share_token"])
    return HttpResponse(request.user.share_token, content_type="text/plain")


@csrf_exempt
@require_POST
def delete_token(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    request.user.share_token = None
    request.user.save(update_fields=["share_token"])
    return HttpResponse()


# ---------------------------------------------------------------------------
# Dashboard preferences
# ---------------------------------------------------------------------------


def _raw_query_string(request) -> str:
    return unquote(request.META.get("QUERY_STRING", ""))


@require_GET
def set_pref_site(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    site = _raw_query_string(request)
    if site:
        request.user.prefs["site"] = site
        request.user.save(update_fields=["prefs"])
    return HttpResponse()


@require_GET
def set_pref_range(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    pref_range = _raw_query_string(request)
    if pref_range:
        request.user.prefs["range"] = pref_range
        request.user.save(update_fields=["prefs"])
    return HttpResponse()


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


@require_GET
def lang(request):
    """Best-effort viewer country code from Accept-Language (e.g. 'RU')."""
    header = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for part in header.split(","):
        region = part.split(";")[0].strip().split("-")[-1]
        if region and region.isalpha() and len(region) == 2 and region.isupper():
            return HttpResponse(region, content_type="text/plain")
    return HttpResponse("EN", content_type="text/plain")


@csrf_exempt
@require_POST
def newsletter_register(request):
    mail = request.POST.get("mail", "").strip()
    if not mail:
        return error("Mail is required")
    NewsletterSubscriber.objects.get_or_create(mail=mail)
    return HttpResponse()


@csrf_exempt
@require_POST
def subscribed(request):
    if not request.user.is_authenticated:
        return error("Not signed in", 403)
    subscription_id = request.POST.get("subscription_id", "").strip()
    if not subscription_id:
        return error("subscription_id is required")
    request.user.subscription_id = subscription_id
    request.user.save(update_fields=["subscription_id"])
    return HttpResponse()
