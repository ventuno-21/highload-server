from rest_framework import serializers
from .models import Item, RequestLog


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class RequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLog
        fields = "__all__"


class MongoEventSerializer(serializers.Serializer):
    type = serializers.CharField()
    ts = serializers.FloatField()
    name = serializers.CharField(required=False)
