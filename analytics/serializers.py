from rest_framework import serializers

from .models import Site


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "domain", "allowed_domains", "filter_allowed_domains"]
        read_only_fields = ["id"]


class IngressEntrySerializer(serializers.Serializer):
    user = serializers.CharField()
    site = serializers.CharField()
    metric = serializers.CharField(max_length=64)
    value = serializers.CharField(max_length=255)
    incr = serializers.IntegerField()
