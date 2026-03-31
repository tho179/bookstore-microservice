from django.db import models


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_FAILED = "failed"

    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=40, default="cod")
    shipping_method = models.CharField(max_length=40, default="standard")
    shipping_address = models.TextField(blank=True, default="")
    payment_id = models.IntegerField(null=True, blank=True)
    shipment_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.IntegerField()
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=60, blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)