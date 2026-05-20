from rest_framework import serializers

from .models import Host


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ["name"]


class IngressRequestSerializer(serializers.Serializer):
    user = serializers.CharField()
    host = serializers.CharField()
    metric = serializers.CharField()
    value = serializers.CharField()
    incr = serializers.IntegerField()


class QueryRequestSerializer(serializers.Serializer):
    site = serializers.CharField()
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
