"""Input validation for the API views (docs/api.md)."""
from rest_framework.serializers import BooleanField, CharField, IntegerField, Serializer


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


class AccountEditSerializer(Serializer):
    utcoffset = IntegerField(required=False, default=0)
    usesites = BooleanField(required=False, default=False)
    sites = CharField(required=False, allow_blank=True, default="")
    mail = CharField(required=False, allow_blank=True, default="")


class FeedbackSerializer(Serializer):
    feedback = CharField()
    contact = CharField(required=False, allow_blank=True, default="")


class SubscribedSerializer(Serializer):
    subscription_id = CharField()


class NewsletterSerializer(Serializer):
    mail = CharField()