import json
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.parse import unquote

from django.core.cache import cache
from django.db.models import Sum
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Count, Host
from .serializers import HostSerializer, QueryRequestSerializer


class HostViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = HostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Host.objects.filter(user=self.request.user)
        if self.request.user.hide_hosts:
            qs = qs.filter(hide=False)
        return qs.order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        if request.method == "PUT":
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def query(request):
    serializer = QueryRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    site = serializer.validated_data["site"]
    start = serializer.validated_data.get("start_date")
    end = serializer.validated_data.get("end_date")

    host = get_object_or_404(Host, name=site, user=request.user)

    qs = Count.objects.filter(host=host)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    result: dict[str, dict[str, int]] = defaultdict(dict)
    rows = qs.values("category", "item").annotate(total=Sum("total"))
    for row in rows:
        result[row["category"]][row["item"]] = row["total"]

    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def visit_logs(request):
    """
    Retrieve recent visit log entries from Redis for sites owned by
    the authenticated user.

    Each entry is a timestamped log line in the format:
        [YYYY-MM-DD HH:MM:SS] <country> <referrer> <device> <platform>

    Query params:
        site (optional) - filter logs for a specific hostname
        limit (optional) - max number of log entries to return (default: 30)
    """
    site_filter = request.query_params.get("site")
    limit_str = request.query_params.get("limit", "30")
    try:
        limit = max(1, min(int(limit_str), 100))
    except (ValueError, TypeError):
        limit = 30

    try:
        redis = cache._cache.get_client()
    except Exception:
        return Response({"error": "Cache backend not available"}, status=500)

    logs = []
    user = request.user
    hosts = Host.objects.filter(user=user)
    if site_filter:
        hosts = hosts.filter(name=site_filter)

    if not hosts:
        return Response({"logs": [], "sites_with_logs": []})

    sites_with_logs = []
    for host in hosts:
        log_key = f"log:{host.name}:{user.username}"
        try:
            entries = redis.zrevrange(log_key, 0, limit - 1, withscores=True)
        except Exception:
            entries = []

        if entries:
            sites_with_logs.append(host.name)

        for entry_bytes, score in entries:
            try:
                log_line = entry_bytes.decode("utf-8", errors="replace")
            except Exception:
                continue

            log_entry = parse_log_line(log_line)
            if log_entry:
                log_entry["site"] = host.name
                logs.append(log_entry)

    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    logs = logs[:limit]

    return Response({
        "logs": logs,
        "sites_with_logs": sites_with_logs,
    })


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


def _query_site_data(host: Host, start: date, end: date) -> dict[str, dict[str, int]]:
    """Query aggregated data for a single host within a date range."""
    qs = Count.objects.filter(host=host, date__gte=start, date__lte=end)
    result: dict[str, dict[str, int]] = defaultdict(dict)
    rows = qs.values("category", "item").annotate(total=Sum("total"))
    for row in rows:
        result[row["category"]][row["item"]] = row["total"]
    return dict(result)


def _get_user_logs(request, user, site: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
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


def _build_dump_payload(request, user) -> dict[str, Any]:
    """
    Build a data dump payload similar to the old /dump SSE endpoint.

    Returns a dict with:
      - user: user info (uuid, prefs)
      - meta: session info (utcoffset from query params)
      - sites: dict keyed by host name, with visits for day, yesterday, all time
    """
    hosts = Host.objects.filter(user=user)
    if user.hide_hosts:
        hosts = hosts.filter(hide=False)

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    # Parse utcoffset from query params (default 0)
    try:
        utcoffset = int(request.GET.get("utcoffset", "0"))
    except (ValueError, TypeError):
        utcoffset = 0

    sites_data: dict[str, dict[str, Any]] = {}
    for host in hosts:
        day_data = _query_site_data(host, today, today)
        yesterday_data = _query_site_data(host, yesterday, yesterday)
        all_data = _query_site_data(host, date(2000, 1, 1), today + timedelta(days=365))

        # Fetch recent logs for this host
        logs = _get_user_logs(request, user, site=host.name, limit=30)

        sites_data[host.name] = {
            "visits": {
                "day": day_data,
                "yesterday": yesterday_data,
                "all": all_data,
            },
            "logs": logs,
        }

    return {
        "user": {
            "uuid": str(user.uuid) if user.uuid else "",
            "prefs": {
                "utcoffset": utcoffset,
            },
        },
        "meta": {
            "utcoffset": utcoffset,
        },
        "sites": sites_data,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dump_sse(request):
    """
    Server-Sent Events endpoint that streams aggregated data.

    This replicates the old `/dump` SSE endpoint, providing real-time
    aggregated data for the authenticated user.

    Query params:
        utcoffset (optional) - user's UTC offset (default: 0)

    The endpoint sends two event types:
      - "dump": full aggregated data payload (on connect and every ~15s)
      - "archive": historical archive data (on connect)

    On error or if user is not found, sends "nouser" event.

    Usage on frontend:
        const source = new EventSource('/api/core/dump/?utcoffset=1');
        source.addEventListener('dump', (e) => {
          const data = JSON.parse(e.data);
          // update dashboard
        });
    """
    user = request.user

    def event_stream():
        interval = 15  # seconds between refreshes

        # Send initial dump immediately
        try:
            payload = _build_dump_payload(request, user)
            yield f"event: dump\ndata: {json.dumps(payload)}\n\n"
        except Exception:
            yield "event: nouser\ndata: {}\n\n"
            return

        # Send archive event (empty for now, old archive logic can be added)
        yield f"event: archive\ndata: {json.dumps({})}\n\n"

        # Stream updates every `interval` seconds
        while True:
            time.sleep(interval)
            try:
                payload = _build_dump_payload(request, user)
                yield f"event: dump\ndata: {json.dumps(payload)}\n\n"
            except Exception:
                yield "event: nouser\ndata: {}\n\n"
                break

    response = StreamingHttpResponse(
        streaming_content=event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["X-Accel-Buffering"] = "no"
    return response
