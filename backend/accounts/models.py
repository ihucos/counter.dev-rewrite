import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


def _new_user_id() -> str:
    return uuid.uuid4().hex


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password, email=None, **extra):
        if not username:
            raise ValueError("Username is required")
        user = self.model(
            username=username,
            email=self.normalize_email(email) if email else None,
            **extra,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, email=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(username, password, email, **extra)

    def create_superuser(self, username, password=None, email=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create_user(username, password, email, **extra)


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

    objects = UserManager()

    REQUIRED_FIELDS: list[str] = []  # email is optional

    def __str__(self) -> str:
        return self.username
