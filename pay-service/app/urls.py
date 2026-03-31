from django.urls import path

from .views import CancelPayment, HealthCheck, ReservePayment

urlpatterns = [
    path("health/", HealthCheck.as_view()),
    path("payments/reserve/", ReservePayment.as_view()),
    path("payments/<int:payment_id>/cancel/", CancelPayment.as_view()),
]
