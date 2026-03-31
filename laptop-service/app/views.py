from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from .models import LaptopProduct
from .serializers import LaptopProductSerializer


class LaptopProductViewSet(viewsets.ModelViewSet):
    queryset = LaptopProduct.objects.all()
    serializer_class = LaptopProductSerializer


@api_view(['GET'])
def health(request):
    return JsonResponse({'status': 'ok', 'service': 'laptop-service'})
