from decimal import Decimal, InvalidOperation

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import PaymentSerializer


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


class HealthCheck(APIView):
    def get(self, request):
        return Response({"service": "pay-service", "status": "ok"})


class ReservePayment(APIView):
    def post(self, request):
        order_id = _to_int(request.data.get("order_id"), 0)
        customer_id = _to_int(request.data.get("customer_id"), 0)
        amount = _to_decimal(request.data.get("amount"))
        method = (request.data.get("method") or "cod").strip() or "cod"

        if order_id <= 0 or customer_id < 0 or amount is None:
            return Response({"error": "order_id, customer_id and amount are required."}, status=status.HTTP_400_BAD_REQUEST)
        if amount < 0:
            return Response({"error": "amount must be >= 0."}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            method=method,
            status=Payment.STATUS_RESERVED,
        )
        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelPayment(APIView):
    def post(self, request, payment_id):
        payment = Payment.objects.filter(id=payment_id).first()
        if not payment:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        payment.status = Payment.STATUS_CANCELLED
        payment.save(update_fields=["status", "updated_at"])
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)