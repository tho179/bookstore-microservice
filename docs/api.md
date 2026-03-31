# API Summary

## Laptop Service

- `GET /health/`
- `GET /products/`
- `POST /products/`
- `GET /products/<id>/`
- `PUT /products/<id>/`
- `PATCH /products/<id>/`
- `DELETE /products/<id>/`

## Mobile Service

- `GET /health/`
- `GET /products/`
- `POST /products/`
- `GET /products/<id>/`
- `PUT /products/<id>/`
- `PATCH /products/<id>/`
- `DELETE /products/<id>/`

## Staff Service

- `GET /health/`
- `GET /staff/`
- `POST /staff/`

## Customer Service

- `GET /health/`
- `GET /customers/`
- `POST /customers/`

## Cart Service

- `GET /health/`
- `POST /carts/` (create or get cart by `customer_id`)
- `GET /carts/<customer_id>/`
- `DELETE /carts/<customer_id>/items/` (clear cart)
- `POST /cart-items/`
- `PUT /cart-items/<item_id>/`
- `DELETE /cart-items/<item_id>/`

## Pay Service

- `GET /health/`
- `POST /payments/reserve/`
- `POST /payments/<payment_id>/cancel/`

## Ship Service

- `GET /health/`
- `POST /shipments/reserve/`
- `POST /shipments/<shipment_id>/cancel/`

## Order Service

- `GET /health/`
- `GET /orders/?customer_id=<id>`
- `POST /orders/`
- `GET /customers/<customer_id>/purchased-products/`

## Comment Rate Service

- `GET /health/`
- `GET /reviews/?customer_id=<id>&product_id=<id>`
- `POST /reviews/`

## Example Payloads

### Create Staff

```json
{
  "name": "Le Van B",
  "email": "b@example.com",
  "department": "operations"
}
```

### Create Customer

```json
{
  "name": "Nguyen Van A",
  "email": "a@example.com"
}
```

### Create Laptop/Mobile Product

```json
{
  "name": "Laptop Pro 14",
  "description": "Laptop van phong",
  "price": "18990000",
  "stock": 10,
  "brand": "ProTech",
  "model_code": "LP14-2026",
  "warranty_months": 24,
  "specs": {
    "ram": "16GB",
    "storage": "512GB SSD"
  },
  "is_active": true
}
```

### Add Item To Cart

```json
{
  "cart": 1,
  "product_id": 1000001,
  "quantity": 2
}
```

### Create Order

```json
{
  "customer_id": 1,
  "total_amount": "37980000.00",
  "payment_method": "cod",
  "shipping_method": "standard",
  "shipping_address": "Hanoi",
  "items": [
    {
      "product_id": 1000001,
      "name": "Laptop Pro 14",
      "category": "Laptop",
      "price": "18990000.00",
      "quantity": 2,
      "line_total": "37980000.00"
    }
  ]
}
```

### Create Review

```json
{
  "customer_id": 1,
  "product_id": 1000001,
  "rating": 5,
  "comment": "good"
}
```
