from django.contrib import admin
from .models import MobileProduct


@admin.register(MobileProduct)
class MobileProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'warranty_months', 'stock')
    search_fields = ('name', 'brand', 'model_code')
