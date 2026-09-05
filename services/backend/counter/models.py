import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    # Whole hours, matching the tracking script's data-utcoffset and the
    # tracker's clamping (-12..14).
    timezone = models.IntegerField(default=0, help_text="UTC offset in hours")
    prefs = models.JSONField(default=dict, blank=True)
    hide_hosts = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, default="")
