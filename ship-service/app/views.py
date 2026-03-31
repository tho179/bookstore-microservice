from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shipment
from .serializers import ShipmentSerializer


def _to_int(raw_value, default=0):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


class HealthCheck(APIView):
    def get(self, request):
        return Response({"service": "ship-service", "status": "ok"})


class ReserveShipment(APIView):
    def post(self, request):
        order_id = _to_int(request.data.get("order_id"), 0)
        customer_id = _to_int(request.data.get("customer_id"), 0)
        address = (request.data.get("address") or "").strip()
        method = (request.data.get("method") or "standard").strip() or "standard"

        if order_id <= 0 or customer_id < 0:
            return Response({"error": "order_id and customer_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        shipment = Shipment.objects.create(
            order_id=order_id,
            customer_id=customer_id,
            address=address,
            method=method,
            status=Shipment.STATUS_RESERVED,
        )
        serializer = ShipmentSerializer(shipment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelShipment(APIView):
    def post(self, request, shipment_id):
        shipment = Shipment.objects.filter(id=shipment_id).first()
        if not shipment:
            return Response({"error": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)

        shipment.status = Shipment.STATUS_CANCELLED
        shipment.save(update_fields=["status", "updated_at"])
        serializer = ShipmentSerializer(shipment)
        return Response(serializer.data)