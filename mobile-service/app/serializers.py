from rest_framework import serializers
from .models import MobileProduct


class MobileProductSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()

    class Meta:
        model = MobileProduct
        fields = [
            'id', 'name', 'description', 'image_url', 'price', 'stock',
            'brand', 'model_code', 'warranty_months', 'specs', 'is_active', 'category'
        ]

    def get_category(self, obj):
        return 'mobile'
