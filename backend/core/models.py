from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet


class Host(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=253)

    class Meta:
        unique_together = [("user", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"


class CountQuerySet(QuerySet):
    pass


class Count(models.Model):
    objects = CountQuerySet.as_manager()
    host = models.ForeignKey(
        Host,
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    metric = models.CharField(max_length=64)
    value = models.CharField(max_length=255)
    count = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [("host", "date", "metric", "value")]
        indexes = [
            models.Index(fields=["host", "date"]),
            models.Index(fields=["host", "metric"]),
        ]

    def __str__(self) -> str:
        return f"{self.host.user.username} {self.host.name} {self.date} {self.metric} {self.value} ({self.count})"
