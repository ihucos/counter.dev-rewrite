from rest_framework import serializers

from .models import Host


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ["id", "name", "hide"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        """Normalize domain name: strip protocol, trailing slashes, etc."""
        # Remove protocol prefix if present
        for prefix in ["https://", "http://", "www."]:
            if value.startswith(prefix):
                value = value[len(prefix) :]
        # Remove trailing slash
        value = value.rstrip("/")
        return value


class QueryRequestSerializer(serializers.Serializer):
    site = serializers.CharField()
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
