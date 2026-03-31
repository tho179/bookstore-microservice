from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from .models import MobileProduct
from .serializers import MobileProductSerializer


class MobileProductViewSet(viewsets.ModelViewSet):
    queryset = MobileProduct.objects.all()
    serializer_class = MobileProductSerializer


@api_view(['GET'])
def health(request):
    return JsonResponse({'status': 'ok', 'service': 'mobile-service'})
