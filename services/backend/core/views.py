import json
import secrets
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.parse import unquote, urlparse

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
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


def _sites_for(user):
    hosts = Host.objects.filter(user=user)
    if user.hide_hosts:
        hosts = hosts.filter(hide=False)
    return hosts.order_by("name")


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
def logout_view(request):
    """End the session. Reached via the navbar's plain "Sign out" link, so
    accept GET and send the browser back to the SPA it came from."""
    if request.user.is_authenticated:
        logout(request)
    referer = request.headers.get("referer", "")
    try:
        parts = urlparse(referer)
        origin = f"{parts.scheme}://{parts.netloc}" if parts.netloc else ""
    except ValueError:
        origin = ""
    return redirect(f"{origin or 'https://counter.dev'}/welcome.html")


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


def _demo_user(request):
    """Resolve demo access (?demo=1) to the seeded "demo" account, if any."""
    if request.GET.get("demo") not in ("1", "true"):
        return None
    return User.objects.filter(username="demo").first()


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


def _resolve_account(request):
    """Resolve the account a dashboard-data request acts on.

    Order: the session user, then guest/share access via
    ?user=<uuid>&token=<token>, then demo access via ?demo=1 (the seeded
    "demo" account, read-only). Returns (user, sessionless, demo); user is
    None when nothing matched.
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


@require_GET
def me_view(request):
    """The signed-in user's state: user record and session meta.

    Feeds session bootstrap (401 means "not signed in") and the
    share-account panel.
    """
    user, sessionless, demo = _resolve_account(request)
    if user is None:
        return _error("not signed in", 401)
    return _json(
        {
            "user": {
                "id": user.username,
                "uuid": str(user.uuid) if user.uuid else "",
                "token": user.share_token,
                "prefs": user.prefs or {},
                "timezone": user.timezone,
            },
            "meta": {
                "utcoffset": _utcoffset(request),
                "sessionless": sessionless,
                "demo": demo,
            },
        }
    )


@require_GET
def query_view(request):
    """Analytics data for one site over an open-ended date range.

    Params: site (required), start and end (ISO dates; either or both may be
    omitted). Returns the Count-model aggregates grouped by the tracker
    categories, plus the recent-visits log from Redis.
    """
    user, sessionless, demo = _resolve_account(request)
    if user is None:
        return _error("not signed in", 401)

    site = request.GET.get("site", "")
    hosts = {h.name: h for h in _sites_for(user)}
    if site not in hosts:
        return _error("no such site")

    try:
        start = date.fromisoformat(request.GET["start"]) if request.GET.get("start") else None
        end = date.fromisoformat(request.GET["end"]) if request.GET.get("end") else None
    except ValueError:
        return _error("invalid date")
    # Open-ended: missing bounds fall back to the same "all" window the
    # dashboard previously used.
    start = start or date(2000, 1, 1)
    end = end or _local_date(_utcoffset(request)) + timedelta(days=365)

    visits = _query_site_data(hosts[site], start, end)
    for category in CATEGORIES:
        visits.setdefault(category, {})
    return _json(
        {
            "site": site,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "visits": visits,
            "logs": _get_user_logs(user, site=site, limit=30),
        }
    )


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