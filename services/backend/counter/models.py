import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

# Dashboard date-range presets, shared with the frontend's selector.
RANGES = ["day", "yesterday", "last7", "last30", "month", "year", "all"]


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    # Whole hours, matching the tracking script's data-utcoffset and the
    # tracker's clamping (-12..14).
    timezone = models.IntegerField(default=0, help_text="UTC offset in hours")
    subscription_id = models.CharField(max_length=64, blank=True, default="")
    hide_hosts = models.BooleanField(default=False)
    # "Limit listed domains": when true, only the Host rows count as the
    # account's sites; when false, all incoming traffic is shown.
    use_sites = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, default="")
    date_range = models.CharField(
        max_length=16,
        choices=[(value, value) for value in RANGES],
        default="day",
    )
    # The dashboard's selected site. Null means "no site selected"; deleting
    # the Host clears the selection automatically (SET_NULL).
    selected_site = models.ForeignKey(
        "core.Host",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
