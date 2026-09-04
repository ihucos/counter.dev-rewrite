import json
import secrets
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.parse import unquote

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django.conf import settings

from .models import Count, Host

User = get_user_model()

RANGES = ["day", "yesterday", "last7", "last30", "month", "year", "all"]


def _plain(message, status=200):
    return HttpResponse(message, status=status, content_type="text/plain")


def _error(message, status=400):
    return HttpResponseBadRequest(message, content_type="text/plain") if status == 400 else _plain(message, status)


def _json(data, status=200):
    return HttpResponse(json.dumps(data), status=status, content_type="application/json")


def _field(request, name):
    """Get a field from a form or JSON body."""
    if request.content_type == "application/json":
        try:
            body = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return None
        return body.get(name)
    return request.POST.get(name)


def _utcoffset(request):
    try:
        return int(request.GET.get("utcoffset", "0"))
    except (ValueError, TypeError):
        return 0


def _local_date(utcoffset_minutes):
    """Today's date in the viewer's timezone, from a UTC offset in minutes."""
    return (timezone.now() + timedelta(minutes=utcoffset_minutes)).date()


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


def _sites_for(user):
    hosts = Host.objects.filter(user=user)
    if user.hide_hosts:
        hosts = hosts.filter(hide=False)
    return hosts.order_by("name")


def _build_dump_payload(utcoffset, user, from_date=None, to_date=None) -> dict[str, Any]:
    """
    Build the full account state: user record, preferences, and visit data.

    Visits are bucketed by the client's local time (utcoffset in minutes).
    Custom range requests additionally include a "custom" bucket.
    """
    today = _local_date(utcoffset)
    yesterday = today - timedelta(days=1)

    sites_data: dict[str, dict[str, Any]] = {}
    for host in _sites_for(user):
        visits = {
            "day": _query_site_data(host, today, today),
            "yesterday": _query_site_data(host, yesterday, yesterday),
            "last7": _query_site_data(host, today - timedelta(days=6), today),
            "last30": _query_site_data(host, today - timedelta(days=29), today),
            "month": _query_site_data(host, today.replace(day=1), today),
            "year": _query_site_data(host, today.replace(month=1, day=1), today),
            "all": _query_site_data(host, date(2000, 1, 1), today + timedelta(days=365)),
        }
        if from_date:
            visits["custom"] = _query_site_data(host, from_date, to_date or from_date)
        sites_data[host.name] = {
            "visits": visits,
            "logs": _get_user_logs(user, site=host.name, limit=30),
        }

    return {
        "user": {
            "uuid": str(user.uuid) if user.uuid else "",
            "prefs": user.prefs or {},
            "timezone": user.timezone,
        },
        "meta": {
            "utcoffset": utcoffset,
            "range": user.prefs.get("range", "day") if user.prefs else "day",
        },
        "sites": sites_data,
    }


# --- Authentication & account -------------------------------------------------


@csrf_exempt
@require_POST
def login_view(request):
    user = request.POST.get("user")
    password = request.POST.get("password")
    if not user or not password:
        return _error("missing fields")
    account = authenticate(request, username=user, password=password)
    if account is None:
        if not User.objects.filter(username=user).exists():
            return _error("no such user")
        return _error("wrong password")
    login(request, account)
    return _plain("ok")


@csrf_exempt
@require_POST
def register_view(request):
    user = request.POST.get("user")
    password = request.POST.get("password")
    mail = request.POST.get("mail") or ""
    try:
        utcoffset = int(request.POST.get("utcoffset", "0"))
    except (ValueError, TypeError):
        return _error("invalid utcoffset")
    if not user or not password:
        return _error("missing fields")
    if User.objects.filter(username=user).exists():
        return _error("user already exists")
    account = User.objects.create_user(username=user, email=mail, password=password)
    account.timezone = utcoffset
    account.save(update_fields=["timezone"])
    login(request, account)
    return _plain("ok")


@csrf_exempt
@require_POST
def recover_view(request):
    mail = request.POST.get("mail")
    user = request.POST.get("user")
    if not mail or not user:
        return _error("missing fields")
    account = User.objects.filter(username=user, email=mail).first()
    if account is not None:
        send_mail(
            "counter.dev account recovery",
            f"Recovery was requested for the account {account.username}.\n"
            f"If this was you, sign in at {settings.PASSWORD_RESET_URL_BASE} "
            "to reset your password.",
            settings.DEFAULT_FROM_EMAIL,
            [mail],
            fail_silently=True,
        )
    return _plain("ok")


@csrf_exempt
@require_POST
def account_edit_view(request):
    user = request.user
    if not user.is_authenticated:
        return _error("not signed in", 403)
    try:
        utcoffset = int(request.POST.get("utcoffset", "0"))
    except (ValueError, TypeError):
        return _error("invalid utcoffset")
    usesites = request.POST.get("usesites", "false").lower() in ("true", "1", "on")
    sites = request.POST.get("sites") or ""
    mail = request.POST.get("mail") or ""

    user.timezone = utcoffset
    user.email = mail
    prefs = dict(user.prefs or {})
    prefs["usesites"] = usesites
    user.prefs = prefs

    names = [_normalize_domain(s.strip()) for s in sites.splitlines() if s.strip()]
    existing = {h.name: h for h in Host.objects.filter(user=user)}
    for name in names:
        if name not in existing:
            Host.objects.create(user=user, name=name)
    for name, host in existing.items():
        if name not in names:
            host.delete()

    user.save()
    return _plain("ok")


@csrf_exempt
@require_POST
def delete_user_view(request):
    if not request.user.is_authenticated:
        return _error("not signed in", 403)
    request.user.delete()
    return _plain("ok")


@csrf_exempt
@require_POST
def feedback_view(request):
    feedback = request.POST.get("feedback")
    if not feedback:
        return _error("missing feedback")
    contact = request.POST.get("contact") or ""
    send_mail(
        "counter.dev feedback",
        f"{feedback}\n\nReply-to: {contact}",
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        fail_silently=True,
    )
    return _plain("ok")


# --- Sites ---------------------------------------------------------------------


@csrf_exempt
@require_POST
def delete_site_view(request):
    user = request.user
    if not user.is_authenticated:
        return _error("not signed in", 403)
    site = (user.prefs or {}).get("site")
    if not site:
        return _error("no site selected")
    host = Host.objects.filter(user=user, name=site).first()
    if host is None:
        return _error("no such site")
    host.delete()  # cascades to its Count rows
    return _plain("ok")


# --- Guest / share access --------------------------------------------------------


@csrf_exempt
@require_POST
def reset_token_view(request):
    user = request.user
    if not user.is_authenticated:
        return _error("not signed in", 403)
    user.share_token = secrets.token_urlsafe(24)
    user.save(update_fields=["share_token"])
    return _json({"token": user.share_token})


@csrf_exempt
@require_POST
def delete_token_view(request):
    user = request.user
    if not user.is_authenticated:
        return _error("not signed in", 403)
    user.share_token = ""
    user.save(update_fields=["share_token"])
    return _plain("ok")


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


# --- Dashboard preferences -------------------------------------------------------


@require_GET
def set_pref_site_view(request):
    # The site name is the raw URL-encoded query string, e.g. /set_pref_site?example.com
    site = request.GET.get("site") or request.META.get("QUERY_STRING", "")
    site = unquote(site).strip()
    if not request.user.is_authenticated:
        return _error("not signed in", 403)
    prefs = dict(request.user.prefs or {})
    prefs["site"] = site
    request.user.prefs = prefs
    request.user.save(update_fields=["prefs"])
    return _plain("ok")


@require_GET
def set_pref_range_view(request):
    value = request.GET.get("range") or request.META.get("QUERY_STRING", "")
    value = unquote(value).strip()
    if value not in RANGES:
        return _error("invalid range")
    if not request.user.is_authenticated:
        return _error("not signed in", 403)
    prefs = dict(request.user.prefs or {})
    prefs["range"] = value
    request.user.prefs = prefs
    request.user.save(update_fields=["prefs"])
    return _plain("ok")


# --- Dashboard data ---------------------------------------------------------------


@require_GET
def dump_sse(request):
    """
    Server-Sent Events endpoint that streams the full account state.

    Each message is a JSON object: {"type": "<event type>", "payload": {...}}.
    Event types: "signedin" (session established), "dump" (full state, resent
    periodically), "nouser" (no signed-in user).

    Authentication is the session cookie, or guest/share access via
    ?user=<uuid>&token=<token>.
    """
    user = request.user if request.user.is_authenticated else _guest_user(request)
    try:
        utcoffset = _utcoffset(request)
        from_date = date.fromisoformat(request.GET["from"]) if request.GET.get("from") else None
        to_date = date.fromisoformat(request.GET["to"]) if request.GET.get("to") else None
    except ValueError:
        return _error("invalid date")

    def message(event, payload):
        return f"data: {json.dumps({'type': event, 'payload': payload})}\n\n"

    def event_stream():
        if user is None:
            yield message("nouser", {})
            return
        yield message("signedin", {"uuid": str(user.uuid)})
        interval = 15
        while True:
            try:
                payload = _build_dump_payload(utcoffset, user, from_date, to_date)
                yield message("dump", payload)
            except Exception:
                yield message("nouser", {})
                return
            time.sleep(interval)

    response = StreamingHttpResponse(
        streaming_content=event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["X-Accel-Buffering"] = "no"
    return response


# --- Misc -------------------------------------------------------------------------


@require_GET
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
            return _plain(tag.split("-")[1].upper())
        return _plain(tag.upper())
    return _plain("EN")


@csrf_exempt
@require_POST
def newsletter_register_view(request):
    mail = request.POST.get("mail")
    if not mail:
        return _error("missing mail")
    print(f"newsletter subscription: {mail}")
    return _plain("ok")


@csrf_exempt
@require_POST
def subscribed_view(request):
    """Record a PayPal subscription ID after payment approval."""
    subscription_id = request.POST.get("subscription_id")
    if subscription_id is None and request.content_type == "application/json":
        try:
            subscription_id = json.loads(request.body or b"{}").get("subscription_id")
        except json.JSONDecodeError:
            subscription_id = None
    if not subscription_id:
        return _error("missing subscription_id")
    if not request.user.is_authenticated:
        return _error("not signed in", 403)
    prefs = dict(request.user.prefs or {})
    prefs["subscription_id"] = subscription_id
    request.user.prefs = prefs
    request.user.save(update_fields=["prefs"])
    return _plain("ok")