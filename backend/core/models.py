from django.conf import settings
from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Host(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=253)
    hide = models.BooleanField(default=True)

    class Meta:
        unique_together = [("user", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"


class Count(models.Model):
    host = models.ForeignKey(
        Host,
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    category = models.CharField(max_length=64)  # e.g. "Browser"
    item = models.CharField(max_length=255)  # e.g. "Firefox"
    total = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [("host", "date", "category", "item")]
        indexes = [
            models.Index(fields=["host", "date"]),
            models.Index(fields=["host", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.host.user.username} {self.host.name} {self.date} {self.category} {self.item} ({self.total})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    email = models.EmailField(blank=True, null=True)
    timezone = models.IntegerField(default=0, help_text="UTC offset in hours")
    prefs = models.JSONField(default=dict, blank=True)
    allowed_domains = models.JSONField(default=list, blank=True)
    filter_allowed_domains = models.BooleanField(default=False)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
