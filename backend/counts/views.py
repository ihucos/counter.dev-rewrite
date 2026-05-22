from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from django.db import transaction
from django.db.models import F, Sum
from rest_framework.generics import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User

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

    host = serializer.validated_data["site"]
    start = serializer.validated_data.get("start_date")
    end = serializer.validated_data.get("end_date")

    host = get_object_or_404(Host, name=host, user=request.user)

    qs = Count.objects.filter(host=host)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    result: dict[str, dict[str, int]] = defaultdict(dict)
    rows = qs.values("metric", "value").annotate(total=Sum("count"))
    for row in rows:
        result[row["metric"]][row["value"]] = row["total"]

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
    host_user_pairs = [(e["user"], e["site"]) for e in entries]
    hosts = Host.objects.bulk_create(
        [Host(user_id=u, name=h) for u, h in host_user_pairs],
        ignore_conflicts=True,
    )


# from django.db import connection
#
# updates = {123: 5, 567: 1}
#
# # Flatten the dict into an array of tuples: [(5, 123), (1, 567)]
# data_matrix = [(val, pk) for pk, val in updates.items() if val != 0]
#
# # Build a fast mass-update using a virtual data table
# query = """
#     UPDATE myapp_product AS p
#     SET stock = p.stock + u.increment
#     FROM (VALUES %s) AS u(increment, id)
#     WHERE p.id = u.id;
# """

with connection.cursor() as cursor:
    # execute_values handles parsing the array of tuples instantly (PostgreSQL specific feature)
    cursor.execute(query, [data_matrix])

    # Fetch host objects in bulk
    # ...

    # Just dump the counts

    # Then merge them later
