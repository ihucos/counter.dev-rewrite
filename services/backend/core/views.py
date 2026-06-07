from collections import defaultdict
from urllib.parse import unquote

from django.core.cache import cache
from django.db.models import Sum
from rest_framework.generics import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


from .models import Count, Host
from .serializers import (
    HostSerializer,
    QueryRequestSerializer,
)


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

    The tracker stores log lines as sorted sets in Redis with keys:
        log:<origin>:<user_id>

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
        from datetime import datetime
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
