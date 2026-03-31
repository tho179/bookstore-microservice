from rest_framework import serializers
from .models import LaptopProduct


class LaptopProductSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()

    class Meta:
        model = LaptopProduct
        fields = [
            'id', 'name', 'description', 'image_url', 'price', 'stock',
            'brand', 'model_code', 'warranty_months', 'specs', 'is_active', 'category'
        ]

    def get_category(self, obj):
        return 'laptop'
