from rest_framework import serializers

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "cart", "product_id", "quantity", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "customer_id", "created_at", "updated_at", "items"]