from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from django.db.models import Sum
from rest_framework.generics import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User

from .models import Count, Host
from .permissions import IngressSecretAuthentication
from .serializers import (
    HostSerializer,
    IngressRequestSerializer,
    QueryRequestSerializer,
)


class HostViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Host.objects.filter(user=self.request.user).order_by("name")


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


def _user_today(user: User) -> date:
    """Return today's date in the user's timezone (UTC offset hours)."""
    tz = timezone(timedelta(hours=user.timezone or 0))
    return datetime.now(tz).date()


@api_view(["POST"])
@authentication_classes([IngressSecretAuthentication])
def ingress(request):
    serializer = IngressRequestSerializer(data=request.data, many=True)
    serializer.is_valid(raise_exception=True)
    entries = serializer.validated_data

    # Create host objects
    host_user_pairs = [(e["user"], e["host"]) for e in entries]
    Host.objects.bulk_create(
        [Host(user_id=u, name=h) for u, h in host_user_pairs],
        ignore_conflicts=True,
    )
