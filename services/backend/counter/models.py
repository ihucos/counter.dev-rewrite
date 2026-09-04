import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    timezone = models.IntegerField(default=0, help_text="UTC offset in hours")
    prefs = models.JSONField(default=dict, blank=True)
    hide_hosts = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, null=True)
    subscription_id = models.CharField(max_length=255, blank=True, null=True)


class NewsletterSubscriber(models.Model):
    mail = models.EmailField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.mail


class Feedback(models.Model):
    message = models.TextField()
    contact = models.CharField(max_length=255, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.contact}: {self.message[:50]}"
