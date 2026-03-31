import os

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review
from .serializers import ReviewSerializer

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "5"))
SERVICE_SHARED_TOKEN = os.getenv("SERVICE_SHARED_TOKEN", "")


def _to_int(raw_value, default=0):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _internal_headers():
    if not SERVICE_SHARED_TOKEN:
        return {}
    return {"X-Service-Token": SERVICE_SHARED_TOKEN}


def _purchased_product_ids(customer_id):
    try:
        response = requests.get(
            f"{ORDER_SERVICE_URL}/customers/{customer_id}/purchased-products/",
            timeout=REQUEST_TIMEOUT,
            headers=_internal_headers(),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return None, "Invalid response from order-service."
        ids = payload.get("product_ids", [])
        if not isinstance(ids, list):
            return None, "Invalid purchased-products payload."
        return {_to_int(product_id, 0) for product_id in ids}, None
    except requests.RequestException:
        return None, "Cannot verify purchased products from order-service."


class HealthCheck(APIView):
    def get(self, request):
        return Response({"service": "comment-rate-service", "status": "ok"})


class ReviewListCreate(APIView):
    def get(self, request):
        queryset = Review.objects.all().order_by("-updated_at")

        customer_id = _to_int(request.GET.get("customer_id"), 0)
        product_id = _to_int(request.GET.get("product_id"), 0)
        if customer_id > 0:
            queryset = queryset.filter(customer_id=customer_id)
        if product_id > 0:
            queryset = queryset.filter(product_id=product_id)

        serializer = ReviewSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        customer_id = _to_int(request.data.get("customer_id"), 0)
        product_id = _to_int(request.data.get("product_id"), 0)
        rating = _to_int(request.data.get("rating"), 0)
        comment = (request.data.get("comment") or "").strip()

        if customer_id <= 0 or product_id <= 0:
            return Response({"error": "customer_id and product_id are required."}, status=status.HTTP_400_BAD_REQUEST)
        if rating < 1 or rating > 5:
            return Response({"error": "rating must be between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        purchased_ids, error = _purchased_product_ids(customer_id)
        if purchased_ids is None:
            return Response({"error": error}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if product_id not in purchased_ids:
            return Response({"error": "You can only review purchased products."}, status=status.HTTP_400_BAD_REQUEST)

        review, _ = Review.objects.update_or_create(
            customer_id=customer_id,
            product_id=product_id,
            defaults={"rating": rating, "comment": comment},
        )

        serializer = ReviewSerializer(review)
        return Response(serializer.data)