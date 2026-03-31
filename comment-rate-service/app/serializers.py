from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "customer_id", "product_id", "rating", "comment", "created_at", "updated_at"]