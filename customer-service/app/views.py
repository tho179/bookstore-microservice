from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomerSerializer


class HealthCheck(APIView):
    def get(self, request):
        return Response({"service": "customer-service", "status": "ok"})

class CustomerListCreate(APIView):
    def get(self, request):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)