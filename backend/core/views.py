from collections import defaultdict

from django.db.models import Sum
from rest_framework.generics import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from .models import Count, Host
from .serializers import (
    HostSerializer,
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
