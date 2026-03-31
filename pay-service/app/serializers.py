from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order_id", "customer_id", "amount", "method", "status", "created_at", "updated_at"]