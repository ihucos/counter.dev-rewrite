"""Input validation for the API views (docs/api.md)."""
from rest_framework.serializers import BooleanField, CharField, ChoiceField, IntegerField, Serializer

from counter.models import RANGES


class LoginSerializer(Serializer):
    user = CharField()
    password = CharField()


class RegisterSerializer(Serializer):
    user = CharField()
    password = CharField()
    mail = CharField(required=False, allow_blank=True, default="")
    utcoffset = IntegerField(required=False, default=0)


class RecoverSerializer(Serializer):
    mail = CharField()
    user = CharField()


class AccountUpdateSerializer(Serializer):
    """PUT /account body. Every field is optional: absent fields keep their
    current value, so the SPA's selector can update just site/range."""

    mail = CharField(required=False, allow_blank=True)
    utcoffset = IntegerField(required=False)
    usesites = BooleanField(required=False)
    sites = CharField(required=False, allow_blank=True)
    site = CharField(required=False, allow_blank=True)
    range = ChoiceField(choices=RANGES, required=False)


class FeedbackSerializer(Serializer):
    feedback = CharField()
    contact = CharField(required=False, allow_blank=True, default="")


class SubscribedSerializer(Serializer):
    subscription_id = CharField()


class NewsletterSerializer(Serializer):
    mail = CharField()