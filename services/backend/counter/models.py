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
    prefs = models.JSONField(default=dict, blank=True)
    hide_hosts = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, default="")
    date_range = models.CharField(
        max_length=16,
        choices=[(value, value) for value in RANGES],
        default="day",
    )
    # The dashboard's selected site as a plain name string, not an FK: the
    # value may legitimately not match any Host row (e.g. the demo account's
    # displayed "counter.dev" name), so a FK would reject it.
    selected_site = models.CharField(max_length=253, blank=True, default="")
