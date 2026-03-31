from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "name", "category", "price", "quantity", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.CharField(source="total_amount", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_id",
            "status",
            "total",
            "total_amount",
            "payment_method",
            "shipping_method",
            "shipping_address",
            "payment_id",
            "shipment_id",
            "created_at",
            "updated_at",
            "items",
        ]