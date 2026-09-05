"""Input validation for the API views (docs/api.md)."""
from rest_framework.serializers import BooleanField, CharField, ChoiceField, IntegerField, Serializer

from counter.models import RANGES
from core.models import Host


def _normalize_domain(value):
    for prefix in ["https://", "http://", "www."]:
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.rstrip("/")


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
    """PUT /account body. The field names are the User model's columns; every
    field is optional: absent fields keep their current value, so the SPA's
    selector can update just selected_site/date_range."""

    email = CharField(required=False, allow_blank=True)
    timezone = IntegerField(required=False)
    use_sites = BooleanField(required=False)
    selected_site = CharField(required=False, allow_blank=True)
    date_range = ChoiceField(choices=RANGES, required=False)

    def update(self, instance, validated_data):
        user = instance
        for field in ["timezone", "email", "use_sites", "date_range"]:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        if "selected_site" in validated_data:
            name = _normalize_domain(validated_data["selected_site"].strip())
            user.selected_site = (
                Host.objects.filter(user=user, name=name).first() if name else None
            )
        user.save()
        return user


class FeedbackSerializer(Serializer):
    feedback = CharField()
    contact = CharField(required=False, allow_blank=True, default="")


class SubscribedSerializer(Serializer):
    subscription_id = CharField()


class NewsletterSerializer(Serializer):
    mail = CharField()