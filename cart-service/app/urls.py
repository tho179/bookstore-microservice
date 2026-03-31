from django.urls import path

from .views import (
    CartByCustomer,
    CartClearItems,
    CartItemCreate,
    CartItemDetail,
    CartListCreate,
    HealthCheck,
)

urlpatterns = [
    path("health/", HealthCheck.as_view()),
    path("carts/", CartListCreate.as_view()),
    path("carts/<int:customer_id>/", CartByCustomer.as_view()),
    path("carts/<int:customer_id>/items/", CartClearItems.as_view()),
    path("cart-items/", CartItemCreate.as_view()),
    path("cart-items/<int:item_id>/", CartItemDetail.as_view()),
]
