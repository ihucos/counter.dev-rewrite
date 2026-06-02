from rest_framework import serializers

from .models import Host
from rest_framework import serializers
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model

User = get_user_model()
from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from django.core.exceptions import ValidationError as DjangoValidationError



class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ["id", "name", "hide"]
        read_only_fields = ["id", "name"]


class QueryRequestSerializer(serializers.Serializer):
    site = serializers.CharField()
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class CustomRegisterSerializer(RegisterSerializer):
    timezone = serializers.IntegerField(default=0)
    prefs = serializers.JSONField(default=dict)
    hide_hosts = serializers.BooleanField(default=False)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update({
            'timezone': self.validated_data.get('timezone', 0),
            'prefs': self.validated_data.get('prefs', dict),
            'hide_hosts': self.validated_data.get('hide_hosts', False),
        })
        return data

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        user = adapter.save_user(request, user, self, commit=False)
        if "password1" in self.cleaned_data:
            try:
                adapter.clean_password(self.cleaned_data['password1'], user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    detail=serializers.as_serializer_error(exc)
                )
        user.save()
        self.custom_signup(request, user)
        setup_user_email(request, user, [])

        # Set extra fields
        user.timezone = self.cleaned_data.get('timezone', 0)
        user.prefs = self.cleaned_data.get('prefs', dict)
        user.hide_hosts = self.cleaned_data.get('hide_hosts', False)
        user.save()

        return user


class CustomUserDetailsSerializer(UserDetailsSerializer):
    timezone = serializers.IntegerField(default=0)
    prefs = serializers.JSONField(default=dict)
    hide_hosts = serializers.BooleanField(default=False)

    class Meta(UserDetailsSerializer.Meta):
        model = User
        fields = UserDetailsSerializer.Meta.fields + (
            "timezone",
            "prefs",
            "hide_hosts",
        )

    def update(self, instance, validated_data):
        # Update user fields directly (no profile indirection)
        instance = super().update(instance, validated_data)
        return instance
