from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from django.db import transaction
from django.db.models import F, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User

from .models import Count, Site
from .permissions import IngressSecretAuthentication
from .serializers import IngressEntrySerializer, SiteSerializer


class SiteViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Site.objects.filter(user=self.request.user).order_by("domain")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def _user_today(user: User) -> date:
    """Return today's date in the user's timezone (UTC offset hours)."""
    tz = timezone(timedelta(hours=user.timezone or 0))
    return datetime.now(tz).date()


@api_view(["POST"])
@authentication_classes([IngressSecretAuthentication])
@permission_classes([IsAuthenticated])
def ingress(request):
    serializer = IngressEntrySerializer(data=request.data, many=True)
    serializer.is_valid(raise_exception=True)
    entries = serializer.validated_data

    # Resolve users referenced in the batch (drop entries for unknown users)
    user_ids = {e["user"] for e in entries}
    users = {u.id: u for u in User.objects.filter(id__in=user_ids)}

    # Auto-create missing Site rows for known users
    domains_per_user: dict[str, set[str]] = defaultdict(set)
    for e in entries:
        if e["user"] in users:
            domains_per_user[e["user"]].add(e["site"])

    existing_sites: dict[tuple[str, str], Site] = {}
    if domains_per_user:
        from django.db.models import Q

        q = Q()
        for uid, domains in domains_per_user.items():
            q |= Q(user_id=uid, domain__in=domains)
        for s in Site.objects.filter(q):
            existing_sites[(s.user_id, s.domain)] = s

        to_create = []
        for uid, domains in domains_per_user.items():
            for d in domains:
                if (uid, d) not in existing_sites:
                    to_create.append(Site(user_id=uid, domain=d))
        if to_create:
            Site.objects.bulk_create(to_create, ignore_conflicts=True)
            # Refresh map (bulk_create with ignore_conflicts may not return ids on all DBs)
            for s in Site.objects.filter(q):
                existing_sites[(s.user_id, s.domain)] = s

    # Aggregate increments per (site, date, metric, value)
    buckets: dict[tuple[int, date, str, str], int] = defaultdict(int)
    for e in entries:
        user = users.get(e["user"])
        if not user:
            continue
        site = existing_sites.get((e["user"], e["site"]))
        if not site:
            continue
        bucket_date = _user_today(user)
        buckets[(site.id, bucket_date, e["metric"], e["value"])] += int(e["incr"])

    # Apply increments atomically
    with transaction.atomic():
        for (site_id, d, metric, value), incr in buckets.items():
            updated = Count.objects.filter(
                site_id=site_id, date=d, metric=metric, value=value
            ).update(count=F("count") + incr)
            if not updated:
                Count.objects.create(
                    site_id=site_id, date=d, metric=metric, value=value, count=incr
                )

    return Response({"accepted": len(buckets)}, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def query(request):
    site_id = request.query_params.get("site")
    start = request.query_params.get("start_date")
    end = request.query_params.get("end_date")

    if not site_id:
        return Response({"detail": "site is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        site = Site.objects.get(pk=site_id, user=request.user)
    except Site.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    qs = Count.objects.filter(site=site)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    result: dict[str, dict[str, int]] = defaultdict(dict)
    rows = qs.values("metric", "value").annotate(total=Sum("count"))
    for row in rows:
        result[row["metric"]][row["value"]] = row["total"]

    return Response(result)
