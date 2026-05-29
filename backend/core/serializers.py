from rest_framework import serializers

from .models import Host
from rest_framework import serializers
from dj_rest_auth.serializers import UserDetailsSerializer
from .models import UserProfile


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ["id", "name", "hide"]
        read_only_fields = ["id", "name"]


class QueryRequestSerializer(serializers.Serializer):
    site = serializers.CharField()
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("timezone", "prefs", "hide_hosts")


class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile = UserProfileSerializer()

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ("profile",)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})

        # Update user fields
        instance = super().update(instance, validated_data)

        # Update profile fields
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance
