from rest_framework import serializers

from .models import Shipment


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ["id", "order_id", "customer_id", "address", "method", "status", "created_at", "updated_at"]