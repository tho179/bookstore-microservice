from django.urls import path

from .views import CancelShipment, HealthCheck, ReserveShipment

urlpatterns = [
    path("health/", HealthCheck.as_view()),
    path("shipments/reserve/", ReserveShipment.as_view()),
    path("shipments/<int:shipment_id>/cancel/", CancelShipment.as_view()),
]
