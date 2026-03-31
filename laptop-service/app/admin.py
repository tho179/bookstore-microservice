from django.contrib import admin
from .models import LaptopProduct


@admin.register(LaptopProduct)
class LaptopProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'warranty_months', 'stock')
    search_fields = ('name', 'brand', 'model_code')
