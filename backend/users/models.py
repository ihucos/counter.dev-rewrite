import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


def _new_user_id() -> str:
    return uuid.uuid4().hex


class User(AbstractUser):
    id = models.CharField(
        primary_key=True, max_length=64, default=_new_user_id, editable=False
    )
    email = models.EmailField(blank=True, null=True)
    timezone = models.IntegerField(default=0, help_text="UTC offset in hours")
    prefs = models.JSONField(default=dict, blank=True)
    hide_hosts = models.BooleanField(default=False)

    # IMPORTANT: username cannot be an uid!

    REQUIRED_FIELDS: list[str] = []  # email is optional

    def __str__(self) -> str:
        return self.username
