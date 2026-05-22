from django.conf import settings
from django.db import models


class Host(models.Model):
    class Meta:
        unique_together = [("user", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"


class Count(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosts",
    )
    host = models.CharField(max_length=253)
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
        return f"{self.host_id} {self.date} {self.metric}={self.value} ({self.count})"
