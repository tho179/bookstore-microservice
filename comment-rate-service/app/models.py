from django.db import models


class Review(models.Model):
    customer_id = models.IntegerField()
    product_id = models.IntegerField()
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("customer_id", "product_id")