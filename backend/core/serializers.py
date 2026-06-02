from rest_framework import serializers

from .models import Host
from rest_framework import serializers
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ["id", "name", "hide"]
        read_only_fields = ["id", "name"]


class QueryRequestSerializer(serializers.Serializer):
    site = serializers.CharField()
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


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
