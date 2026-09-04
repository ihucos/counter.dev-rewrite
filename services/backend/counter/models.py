import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    timezone = models.IntegerField(default=0, help_text="UTC offset in minutes")
    prefs = models.JSONField(default=dict, blank=True)
    hide_hosts = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, default="")
