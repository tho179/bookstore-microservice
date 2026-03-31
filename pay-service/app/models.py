from django.db import models


class Payment(models.Model):
    STATUS_RESERVED = "reserved"
    STATUS_CANCELLED = "cancelled"

    order_id = models.IntegerField()
    customer_id = models.IntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=40, default="cod")
    status = models.CharField(max_length=20, default=STATUS_RESERVED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)