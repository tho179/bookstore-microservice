import os
from decimal import Decimal, InvalidOperation

import requests
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import OrderSerializer

PAY_SERVICE_URL = os.getenv("PAY_SERVICE_URL", "http://pay-service:8000")
SHIP_SERVICE_URL = os.getenv("SHIP_SERVICE_URL", "http://ship-service:8000")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "5"))
SERVICE_SHARED_TOKEN = os.getenv("SERVICE_SHARED_TOKEN", "")


def _to_int(raw_value, default=0):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _to_decimal(raw_value):
    try:
        return Decimal(str(raw_value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _internal_headers():
    if not SERVICE_SHARED_TOKEN:
        return {}
    return {"X-Service-Token": SERVICE_SHARED_TOKEN}


def _post_json(url, payload):
    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT, headers=_internal_headers())
        body = response.json() if response.content else {}
        if response.status_code >= 400:
            return False, body, f"{url} failed ({response.status_code})."
        return True, body, None
    except requests.RequestException:
        return False, None, f"Cannot connect to {url}."
    except ValueError:
        return False, None, f"Invalid JSON response from {url}."


class HealthCheck(APIView):
    def get(self, request):
        return Response({"service": "order-service", "status": "ok"})


class OrderListCreate(APIView):
    def get(self, request):
        queryset = Order.objects.all().order_by("-id")
        customer_id = _to_int(request.GET.get("customer_id"), 0)
        if customer_id > 0:
            queryset = queryset.filter(customer_id=customer_id)

        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        customer_id = _to_int(request.data.get("customer_id"), -1)
        items = request.data.get("items")
        if customer_id < 0 or not isinstance(items, list) or not items:
            return Response(
                {"error": "customer_id and non-empty items are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_amount = _to_decimal(request.data.get("total_amount") or request.data.get("total"))
        if total_amount is None or total_amount < 0:
            return Response({"error": "total_amount is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = (request.data.get("payment_method") or "cod").strip() or "cod"
        shipping_method = (request.data.get("shipping_method") or "standard").strip() or "standard"
        shipping_address = (request.data.get("shipping_address") or "").strip()

        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=total_amount,
            payment_method=payment_method,
            shipping_method=shipping_method,
            shipping_address=shipping_address,
            status=Order.STATUS_PENDING,
        )

        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue

            product_id = _to_int(raw_item.get("product_id"), 0)
            quantity = _to_int(raw_item.get("quantity"), 0)
            price = _to_decimal(raw_item.get("price"))
            line_total = _to_decimal(raw_item.get("line_total"))
            name = (raw_item.get("name") or "").strip() or f"Product #{product_id}"
            category = (raw_item.get("category") or "").strip()

            if product_id <= 0 or quantity <= 0 or price is None or line_total is None:
                continue

            OrderItem.objects.create(
                order=order,
                product_id=product_id,
                name=name,
                category=category,
                price=price,
                quantity=quantity,
                line_total=line_total,
            )

        if not order.items.exists():
            order.status = Order.STATUS_FAILED
            order.save(update_fields=["status", "updated_at"])
            return Response({"error": "No valid order items."}, status=status.HTTP_400_BAD_REQUEST)

        pay_ok, pay_data, pay_error = _post_json(
            f"{PAY_SERVICE_URL}/payments/reserve/",
            {
                "order_id": order.id,
                "customer_id": customer_id,
                "amount": str(total_amount),
                "method": payment_method,
            },
        )
        if not pay_ok:
            order.status = Order.STATUS_FAILED
            order.save(update_fields=["status", "updated_at"])
            return Response({"error": pay_error or "Payment reservation failed."}, status=status.HTTP_502_BAD_GATEWAY)

        payment_id = _to_int((pay_data or {}).get("id"), 0)

        ship_ok, ship_data, ship_error = _post_json(
            f"{SHIP_SERVICE_URL}/shipments/reserve/",
            {
                "order_id": order.id,
                "customer_id": customer_id,
                "address": shipping_address,
                "method": shipping_method,
            },
        )
        if not ship_ok:
            if payment_id > 0:
                _post_json(f"{PAY_SERVICE_URL}/payments/{payment_id}/cancel/", {})

            order.status = Order.STATUS_FAILED
            order.payment_id = payment_id if payment_id > 0 else None
            order.save(update_fields=["status", "payment_id", "updated_at"])
            return Response({"error": ship_error or "Shipment reservation failed."}, status=status.HTTP_502_BAD_GATEWAY)

        shipment_id = _to_int((ship_data or {}).get("id"), 0)

        order.status = Order.STATUS_CONFIRMED
        order.payment_id = payment_id if payment_id > 0 else None
        order.shipment_id = shipment_id if shipment_id > 0 else None
        order.save(update_fields=["status", "payment_id", "shipment_id", "updated_at"])

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PurchasedProductsByCustomer(APIView):
    def get(self, request, customer_id):
        order_ids = Order.objects.filter(customer_id=customer_id, status=Order.STATUS_CONFIRMED).values_list("id", flat=True)
        product_ids = (
            OrderItem.objects.filter(order_id__in=order_ids)
            .values_list("product_id", flat=True)
            .distinct()
        )

        return Response(
            {
                "customer_id": customer_id,
                "product_ids": list(product_ids),
            }
        )