import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


def _new_user_id() -> str:
    return uuid.uuid4().hex


class User(AbstractUser):
    # str id allows uuid4 hex for new users and arbitrary legacy strings
    id = models.CharField(
        primary_key=True, max_length=64, default=_new_user_id, editable=False
    )
    email = models.EmailField(blank=True, null=True)
    timezone = models.IntegerField(default=0, help_text="UTC offset in hours")
    prefs = models.JSONField(default=dict, blank=True)
    allowed_domains = models.JSONField(default=list, blank=True)
    filter_allowed_domains = models.BooleanField(default=False)

    # IMPORTANT: username cannot be an uid!

    REQUIRED_FIELDS: list[str] = []  # email is optional

    def __str__(self) -> str:
        return self.username
