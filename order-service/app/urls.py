from django.urls import path

from .views import HealthCheck, OrderListCreate, PurchasedProductsByCustomer

urlpatterns = [
    path("health/", HealthCheck.as_view()),
    path("orders/", OrderListCreate.as_view()),
    path("customers/<int:customer_id>/purchased-products/", PurchasedProductsByCustomer.as_view()),
]
