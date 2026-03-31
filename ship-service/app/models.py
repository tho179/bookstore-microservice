from django.db import models


class Shipment(models.Model):
    STATUS_RESERVED = "reserved"
    STATUS_CANCELLED = "cancelled"

    order_id = models.IntegerField()
    customer_id = models.IntegerField()
    address = models.TextField(blank=True, default="")
    method = models.CharField(max_length=40, default="standard")
    status = models.CharField(max_length=20, default=STATUS_RESERVED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)