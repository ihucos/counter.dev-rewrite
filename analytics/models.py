from django.conf import settings
from django.db import models


class Site(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sites",
    )
    domain = models.CharField(max_length=253)
    allowed_domains = models.JSONField(default=list, blank=True)
    filter_allowed_domains = models.BooleanField(default=False)

    class Meta:
        unique_together = [("user", "domain")]

    def __str__(self) -> str:
        return f"{self.domain} ({self.user_id})"


class Count(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="counts")
    date = models.DateField()
    metric = models.CharField(max_length=64)
    value = models.CharField(max_length=255)
    count = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [("site", "date", "metric", "value")]
        indexes = [
            models.Index(fields=["site", "date"]),
            models.Index(fields=["site", "metric"]),
        ]

    def __str__(self) -> str:
        return f"{self.site_id} {self.date} {self.metric}={self.value} ({self.count})"
