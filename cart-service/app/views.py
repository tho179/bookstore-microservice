from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer


def _to_int(raw_value, default=0):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


class HealthCheck(APIView):
    def get(self, request):
        return Response({"service": "cart-service", "status": "ok"})


class CartListCreate(APIView):
    def get(self, request):
        serializer = CartSerializer(Cart.objects.all().order_by("id"), many=True)
        return Response(serializer.data)

    def post(self, request):
        customer_id = _to_int(request.data.get("customer_id"), -1)
        if customer_id < 0:
            return Response({"error": "customer_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartByCustomer(APIView):
    def get(self, request, customer_id):
        cart = Cart.objects.filter(customer_id=customer_id).first()
        if not cart:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartSerializer(cart)
        return Response(
            {
                "customer_id": cart.customer_id,
                "cart_id": cart.id,
                "items": serializer.data.get("items", []),
            }
        )


class CartClearItems(APIView):
    def delete(self, request, customer_id):
        cart = Cart.objects.filter(customer_id=customer_id).first()
        if not cart:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        deleted_count, _ = cart.items.all().delete()
        return Response({"deleted_items": deleted_count})


class CartItemCreate(APIView):
    @transaction.atomic
    def post(self, request):
        cart_id = _to_int(request.data.get("cart"), 0)
        product_id = _to_int(request.data.get("product_id"), 0)
        quantity = _to_int(request.data.get("quantity"), 1)

        if cart_id <= 0 or product_id <= 0:
            return Response({"error": "cart and product_id are required."}, status=status.HTTP_400_BAD_REQUEST)
        if quantity <= 0:
            return Response({"error": "quantity must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.filter(id=cart_id).first()
        if not cart:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={"quantity": quantity},
        )

        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity", "updated_at"])

        serializer = CartItemSerializer(item)
        return Response(serializer.data)


class CartItemDetail(APIView):
    def put(self, request, item_id):
        quantity = _to_int(request.data.get("quantity"), 0)
        item = CartItem.objects.filter(id=item_id).first()
        if not item:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            item.delete()
            return Response({"deleted": True})

        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        serializer = CartItemSerializer(item)
        return Response(serializer.data)

    def delete(self, request, item_id):
        item = CartItem.objects.filter(id=item_id).first()
        if not item:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)