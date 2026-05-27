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
    category = models.CharField(max_length=64)
    item = models.CharField(max_length=255)
    total = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [("host", "date", "category", "item")]
        indexes = [
            models.Index(fields=["host", "date"]),
            models.Index(fields=["host", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.host.user.username} {self.host.name} {self.date} {self.category} {self.item} ({self.total})"
