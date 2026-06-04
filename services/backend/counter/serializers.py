from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):
    timezone = serializers.IntegerField(default=0)
    prefs = serializers.JSONField(default=dict)
    hide_hosts = serializers.BooleanField(default=False)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update({
            'timezone': self.validated_data.get('timezone', 0),
            'prefs': self.validated_data.get('prefs', dict()),
            'hide_hosts': self.validated_data.get('hide_hosts', False),
        })
        return data

    def save(self, request):
        user = super().save(request)
        user.timezone = self.cleaned_data.get('timezone', 0)
        user.prefs = self.cleaned_data.get('prefs', dict())
        user.hide_hosts = self.cleaned_data.get('hide_hosts', False)
        user.save(update_fields=['timezone', 'prefs', 'hide_hosts'])
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
