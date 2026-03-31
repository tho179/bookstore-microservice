import os
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import requests
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import GatewayAuthenticationForm, GatewayRegistrationForm

LAPTOP_SERVICE_URL = os.getenv("LAPTOP_SERVICE_URL", "http://laptop-service:8000")
MOBILE_SERVICE_URL = os.getenv("MOBILE_SERVICE_URL", "http://mobile-service:8000")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8000")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
COMMENT_RATE_SERVICE_URL = os.getenv("COMMENT_RATE_SERVICE_URL", "http://comment-rate-service:8000")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "5"))
SERVICE_SHARED_TOKEN = os.getenv("SERVICE_SHARED_TOKEN", "")

CATEGORY_OFFSETS = {
    "laptop": 1000000,
    "mobile": 2000000,
}

CATEGORY_LABELS = {
    "laptop": "Laptop",
    "mobile": "Điện thoại",
}

CATEGORY_IMAGE_FALLBACK = {
    "laptop": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=80",
    "mobile": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1200&q=80",
}

ORDER_STATUS_LABELS = {
    "pending": "Chờ xử lý",
    "processing": "Đang xử lý",
    "paid": "Đã thanh toán",
    "shipping": "Đang giao hàng",
    "delivered": "Đã giao hàng",
    "cancelled": "Đã hủy",
    "unknown": "Chưa cập nhật",
}

PAYMENT_METHOD_LABELS = {
    "cod": "Thanh toán khi nhận hàng",
    "bank_transfer": "Chuyển khoản ngân hàng",
    "credit_card": "Thẻ tín dụng",
}

SHIPPING_METHOD_LABELS = {
    "standard": "Tiêu chuẩn (2-4 ngày)",
    "express": "Nhanh (24h - 48h)",
}

CATEGORY_BASE_URL = {
    "laptop": LAPTOP_SERVICE_URL,
    "mobile": MOBILE_SERVICE_URL,
}


def _auth_required_redirect(request):
    if request.user.is_authenticated:
        return None

    messages.error(request, "Vui lòng đăng nhập để sử dụng tính năng này.")
    next_url = quote(request.get_full_path() or "/shop/", safe="/?=&")
    return redirect(f"/auth/login/?next={next_url}")


def _safe_next_url(raw_value, default="/shop/"):
    candidate = str(raw_value or "").strip()
    if not candidate.startswith("/"):
        return default
    return candidate


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _format_decimal(value):
    return f"{value:.2f}"


def _encode_product_id(category, local_id):
    offset = CATEGORY_OFFSETS.get(category, 0)
    return offset + _to_int(local_id, 0)


def _decode_product_id(global_id):
    raw = _to_int(global_id, 0)
    for category, offset in CATEGORY_OFFSETS.items():
        if offset <= raw < offset + 1000000:
            return category, raw - offset
    return None, 0


def _service_request(method, url, params=None, payload=None):
    headers = {}
    if SERVICE_SHARED_TOKEN:
        headers["X-Service-Token"] = SERVICE_SHARED_TOKEN

    try:
        response = requests.request(
            method,
            url,
            params=params,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers=headers,
        )

        data = None
        if response.content:
            try:
                data = response.json()
            except ValueError:
                data = None

        if response.status_code >= 400:
            if isinstance(data, dict) and data.get("error"):
                return None, data["error"]
            return None, f"Yêu cầu thất bại: {method} {url} ({response.status_code})."

        return data, None
    except requests.RequestException:
        return None, f"Không thể kết nối tới {url}."


def _readable_label(value, label_map, default=""):
    key = str(value or "").strip().lower()
    if key in label_map:
        return label_map[key]
    if key:
        return key
    return default


def _normalize_product(row, category):
    local_id = _to_int(row.get("id"), 0)
    if local_id <= 0:
        return None

    price_value = _to_decimal(row.get("price", 0))
    image_url = str(row.get("image_url") or "").strip()
    if not image_url:
        image_url = CATEGORY_IMAGE_FALLBACK.get(category, "")

    return {
        "id": _encode_product_id(category, local_id),
        "local_id": local_id,
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "name": row.get("name") or f"Sản phẩm #{local_id}",
        "description": row.get("description") or "",
        "image_url": image_url,
        "price": _format_decimal(price_value),
        "price_value": price_value,
        "stock": _to_int(row.get("stock"), 0),
        "brand": row.get("brand") or "",
        "model_code": row.get("model_code") or "",
        "warranty_months": _to_int(row.get("warranty_months"), 0),
        "specs": row.get("specs") if isinstance(row.get("specs"), dict) else {},
        "is_active": bool(row.get("is_active", True)),
    }


def _fetch_products_by_category(category):
    base_url = CATEGORY_BASE_URL.get(category)
    if not base_url:
        return [], f"Danh mục không hợp lệ: {category}"

    data, error = _service_request("GET", f"{base_url}/products/")
    if not isinstance(data, list):
        return [], error or f"Phản hồi không hợp lệ từ {base_url}."

    products = []
    for row in data:
        if not isinstance(row, dict):
            continue
        product = _normalize_product(row, category)
        if product:
            products.append(product)

    return products, error


def _fetch_all_products():
    all_products = []
    warnings = []

    for category in ["laptop", "mobile"]:
        products, error = _fetch_products_by_category(category)
        all_products.extend(products)
        if error:
            warnings.append(error)

    all_products.sort(key=lambda item: item["id"])
    return all_products, warnings


def _fetch_product_detail(product_id):
    category, local_id = _decode_product_id(product_id)
    if not category or local_id <= 0:
        return None, "Mã sản phẩm không hợp lệ."

    base_url = CATEGORY_BASE_URL.get(category)
    data, error = _service_request("GET", f"{base_url}/products/{local_id}/")
    if not isinstance(data, dict):
        return None, error or "Không tìm thấy sản phẩm."

    product = _normalize_product(data, category)
    if not product:
        return None, "Không tìm thấy sản phẩm."
    return product, None


def _get_favorite_ids(request):
    raw = request.session.get("favorite_product_ids", [])
    if not isinstance(raw, list):
        return []

    favorites = []
    for item in raw:
        product_id = _to_int(item, 0)
        if product_id > 0:
            favorites.append(product_id)

    return sorted(list(set(favorites)))


def _save_favorite_ids(request, favorites):
    request.session["favorite_product_ids"] = sorted(list(set(favorites)))
    request.session.modified = True


def _fetch_customers():
    data, error = _service_request("GET", f"{CUSTOMER_SERVICE_URL}/customers/")
    if not isinstance(data, list):
        return [], error or "Không thể tải danh sách khách hàng."
    return data, error


def _normalize_email(value):
    return str(value or "").strip().lower()


def _find_customer_id_by_email(email):
    normalized_email = _normalize_email(email)
    if not normalized_email:
        return 0, None

    customers, error = _fetch_customers()
    for customer in customers:
        if not isinstance(customer, dict):
            continue

        customer_email = _normalize_email(customer.get("email"))
        if customer_email != normalized_email:
            continue

        customer_id = _to_int(customer.get("id"), 0)
        if customer_id > 0:
            return customer_id, error

    return 0, error


def _ensure_customer_for_user(user):
    if not user or not user.is_authenticated:
        return 0, None

    email = _normalize_email(user.email)
    if not email:
        return 0, "Tài khoản chưa có email."

    customer_id, list_error = _find_customer_id_by_email(email)
    if customer_id > 0:
        return customer_id, list_error

    payload = {
        "name": (user.first_name or user.username or "Khách hàng").strip(),
        "email": email,
    }
    created, create_error = _service_request("POST", f"{CUSTOMER_SERVICE_URL}/customers/", payload=payload)
    if isinstance(created, dict):
        new_customer_id = _to_int(created.get("id"), 0)
        if new_customer_id > 0:
            return new_customer_id, None

    # If create failed due to a race condition, re-check by email.
    matched_customer_id, match_error = _find_customer_id_by_email(email)
    if matched_customer_id > 0:
        return matched_customer_id, match_error

    return 0, create_error or match_error or list_error


def _resolve_customer_id(request, preferred_customer_id=0):
    if not request.user.is_authenticated:
        request.session["selected_customer_id"] = 0
        request.session.modified = True
        return 0

    preferred = _to_int(preferred_customer_id, 0)
    if preferred > 0:
        request.session["selected_customer_id"] = preferred
        request.session.modified = True
        return preferred

    session_customer_id = _to_int(request.session.get("selected_customer_id"), 0)
    if session_customer_id > 0:
        return session_customer_id

    user_customer_id, _ = _ensure_customer_for_user(request.user)
    if user_customer_id > 0:
        request.session["selected_customer_id"] = user_customer_id
        request.session.modified = True
        return user_customer_id

    customers, _ = _fetch_customers()
    if customers:
        first_customer_id = _to_int(customers[0].get("id"), 0)
        if first_customer_id > 0:
            request.session["selected_customer_id"] = first_customer_id
            request.session.modified = True
            return first_customer_id

    request.session["selected_customer_id"] = 0
    request.session.modified = True
    return 0


def _ensure_remote_cart(customer_id):
    if customer_id < 0:
        return 0, "Mã khách hàng không hợp lệ."

    data, error = _service_request(
        "POST",
        f"{CART_SERVICE_URL}/carts/",
        payload={"customer_id": customer_id},
    )
    if not isinstance(data, dict):
        return 0, error or "Không thể khởi tạo giỏ hàng."

    cart_id = _to_int(data.get("id"), 0)
    if cart_id <= 0:
        return 0, "Mã giỏ hàng do cart-service trả về không hợp lệ."
    return cart_id, None


def _fetch_remote_cart(customer_id):
    cart_id, ensure_error = _ensure_remote_cart(customer_id)
    if cart_id <= 0:
        return {"cart_id": 0, "items": []}, [ensure_error or "Không thể khởi tạo giỏ hàng."]

    data, error = _service_request("GET", f"{CART_SERVICE_URL}/carts/{customer_id}/")
    if not isinstance(data, dict):
        warning = error or "Không thể tải giỏ hàng từ cart-service."
        return {"cart_id": cart_id, "items": []}, [warning]

    items = data.get("items") if isinstance(data.get("items"), list) else []
    return {
        "cart_id": _to_int(data.get("cart_id"), cart_id),
        "customer_id": _to_int(data.get("customer_id"), customer_id),
        "items": items,
    }, []


def _build_cart_items(products, cart_payload):
    product_by_id = {item["id"]: item for item in products}
    raw_items = cart_payload.get("items") if isinstance(cart_payload, dict) else []
    if not isinstance(raw_items, list):
        raw_items = []

    items = []
    total = Decimal("0")
    total_quantity = 0

    for row in raw_items:
        if not isinstance(row, dict):
            continue

        item_id = _to_int(row.get("id"), 0)
        product_id = _to_int(row.get("product_id"), 0)
        quantity = _to_int(row.get("quantity"), 0)
        if quantity <= 0:
            continue

        product = product_by_id.get(product_id)
        if not product:
            continue

        line_total = product["price_value"] * quantity
        total += line_total
        total_quantity += quantity

        items.append(
            {
                "item_id": item_id,
                "product_id": product_id,
                "quantity": quantity,
                "line_total": _format_decimal(line_total),
                "product": product,
            }
        )

    return items, _format_decimal(total), total_quantity


def _fetch_customer_orders(customer_id):
    data, error = _service_request("GET", f"{ORDER_SERVICE_URL}/orders/", params={"customer_id": customer_id})
    if not isinstance(data, list):
        return [], error or "Không thể tải đơn hàng từ order-service."
    return data, None


def _base_context(request, customer_id=None, cart_count=None):
    if not request.user.is_authenticated:
        return {
            "favorite_count": 0,
            "cart_count": 0,
            "favorite_ids": set(),
            "selected_customer_id": 0,
        }

    favorites = _get_favorite_ids(request)
    resolved_customer_id = customer_id
    if resolved_customer_id is None:
        resolved_customer_id = _resolve_customer_id(request)

    resolved_cart_count = cart_count
    if resolved_cart_count is None:
        cart_payload, _ = _fetch_remote_cart(resolved_customer_id)
        raw_items = cart_payload.get("items", [])
        resolved_cart_count = sum(_to_int(item.get("quantity"), 0) for item in raw_items if isinstance(item, dict))

    return {
        "favorite_count": len(favorites),
        "cart_count": resolved_cart_count,
        "favorite_ids": set(favorites),
        "selected_customer_id": resolved_customer_id,
    }


def home(request):
    return redirect("/shop/")


def health(request):
    return JsonResponse({"service": "api-gateway", "status": "ok"})


def auth_login(request):
    if request.user.is_authenticated:
        return redirect("/shop/")

    next_url = _safe_next_url(request.GET.get("next") or request.POST.get("next"), default="/shop/")
    form = GatewayAuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            customer_id, customer_error = _ensure_customer_for_user(user)
            request.session["selected_customer_id"] = customer_id if customer_id > 0 else 0
            request.session.modified = True

            if customer_error:
                messages.warning(
                    request,
                    f"Đăng nhập thành công, nhưng đồng bộ khách hàng gặp lỗi: {customer_error}",
                )
            else:
                messages.success(request, "Đăng nhập thành công.")
            return redirect(next_url)

        messages.error(request, "Thông tin đăng nhập không hợp lệ.")

    context = {
        "form": form,
        "next_url": next_url,
    }
    context.update(_base_context(request, customer_id=0, cart_count=0))
    return render(request, "auth_login.html", context)


def auth_register(request):
    if request.user.is_authenticated:
        return redirect("/shop/")

    next_url = _safe_next_url(request.GET.get("next") or request.POST.get("next"), default="/shop/")
    form = GatewayRegistrationForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)

            customer_id, customer_error = _ensure_customer_for_user(user)
            request.session["selected_customer_id"] = customer_id if customer_id > 0 else 0
            request.session.modified = True

            if customer_error:
                messages.warning(
                    request,
                    f"Đăng ký thành công, nhưng đồng bộ khách hàng gặp lỗi: {customer_error}",
                )
            else:
                messages.success(request, "Đăng ký thành công. Chào mừng bạn!")
            return redirect(next_url)

        messages.error(request, "Thông tin đăng ký không hợp lệ. Vui lòng kiểm tra lại.")

    context = {
        "form": form,
        "next_url": next_url,
    }
    context.update(_base_context(request, customer_id=0, cart_count=0))
    return render(request, "auth_register.html", context)


def auth_logout(request):
    if request.method != "POST":
        return redirect("/shop/")

    logout(request)
    request.session["selected_customer_id"] = 0
    request.session.modified = True
    messages.success(request, "Bạn đã đăng xuất.")
    return redirect("/shop/")


def shop(request):
    products, warnings = _fetch_all_products()
    customer_id = 0
    cart_payload = {"items": []}
    cart_warnings = []

    if request.user.is_authenticated:
        customer_id = _resolve_customer_id(request, request.GET.get("customer_id"))
        cart_payload, cart_warnings = _fetch_remote_cart(customer_id)

    query = (request.GET.get("q") or "").strip().lower()
    category = (request.GET.get("category") or "").strip().lower()

    filtered = products
    if query:
        filtered = [
            product
            for product in filtered
            if query in product["name"].lower() or query in product["brand"].lower()
        ]

    if category in CATEGORY_LABELS:
        filtered = [product for product in filtered if product["category"] == category]

    context = {
        "products": filtered,
        "query": request.GET.get("q", ""),
        "selected_category": category,
        "category_choices": CATEGORY_LABELS,
        "service_warnings": warnings + cart_warnings,
        "customer_id": customer_id,
    }
    cart_count = sum(_to_int(item.get("quantity"), 0) for item in cart_payload.get("items", []))
    context.update(_base_context(request, customer_id=customer_id, cart_count=cart_count))
    return render(request, "shop.html", context)


def product_detail(request, product_id):
    product, error = _fetch_product_detail(product_id)
    if not product:
        messages.error(request, error or "Không tìm thấy sản phẩm.")
        return redirect("/shop/")

    customer_id = 0
    cart_warnings = []
    cart_count = 0

    if request.user.is_authenticated:
        customer_id = _resolve_customer_id(request, request.GET.get("customer_id"))
        cart_payload, cart_warnings = _fetch_remote_cart(customer_id)
        cart_count = sum(_to_int(item.get("quantity"), 0) for item in cart_payload.get("items", []))

    context = {
        "product": product,
        "is_favorite": product_id in _get_favorite_ids(request),
        "service_warnings": cart_warnings,
        "customer_id": customer_id,
    }
    context.update(_base_context(request, customer_id=customer_id, cart_count=cart_count))
    return render(request, "product_detail.html", context)


def favorites_view(request):
    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    products, warnings = _fetch_all_products()
    customer_id = _resolve_customer_id(request, request.GET.get("customer_id"))
    cart_payload, cart_warnings = _fetch_remote_cart(customer_id)
    cart_count = sum(_to_int(item.get("quantity"), 0) for item in cart_payload.get("items", []))

    favorite_ids = set(_get_favorite_ids(request))
    favorites = [product for product in products if product["id"] in favorite_ids]

    context = {
        "favorites": favorites,
        "service_warnings": warnings + cart_warnings,
        "customer_id": customer_id,
    }
    context.update(_base_context(request, customer_id=customer_id, cart_count=cart_count))
    return render(request, "favorites.html", context)


def toggle_favorite(request, product_id):
    if request.method != "POST":
        return redirect("/shop/")

    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    favorites = _get_favorite_ids(request)
    if product_id in favorites:
        favorites = [item for item in favorites if item != product_id]
        messages.success(request, "Đã xóa khỏi danh sách yêu thích.")
    else:
        favorites.append(product_id)
        messages.success(request, "Đã thêm vào danh sách yêu thích.")

    _save_favorite_ids(request, favorites)
    next_url = _safe_next_url(request.POST.get("next"), default="/favorites/")
    return redirect(next_url)


def add_to_cart(request, product_id):
    if request.method != "POST":
        return redirect("/shop/")

    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    customer_id = _resolve_customer_id(request, request.POST.get("customer_id"))
    cart_id, cart_error = _ensure_remote_cart(customer_id)
    if cart_id <= 0:
        messages.error(request, cart_error or "Không thể khởi tạo giỏ hàng.")
        return redirect("/cart/")

    quantity = _to_int(request.POST.get("quantity"), 1)
    if quantity <= 0:
        quantity = 1

    _, error = _service_request(
        "POST",
        f"{CART_SERVICE_URL}/cart-items/",
        payload={
            "cart": cart_id,
            "product_id": product_id,
            "quantity": quantity,
        },
    )
    if error:
        messages.error(request, error)
        return redirect("/cart/")

    messages.success(request, "Đã thêm sản phẩm vào giỏ hàng.")
    next_url = _safe_next_url(request.POST.get("next"), default="/cart/")
    return redirect(next_url)


def update_cart_item(request, product_id):
    if request.method != "POST":
        return redirect("/cart/")

    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    quantity = _to_int(request.POST.get("quantity"), 1)
    customer_id = _resolve_customer_id(request)
    cart_payload, cart_warnings = _fetch_remote_cart(customer_id)
    if cart_warnings:
        messages.error(request, cart_warnings[0])
        return redirect("/cart/")

    matched = None
    for row in cart_payload.get("items", []):
        if _to_int(row.get("product_id"), 0) == product_id:
            matched = row
            break

    if not matched:
        messages.error(request, "Không tìm thấy sản phẩm trong giỏ hàng.")
        return redirect("/cart/")

    item_id = _to_int(matched.get("id"), 0)
    if item_id <= 0:
        messages.error(request, "Thông tin giỏ hàng không hợp lệ.")
        return redirect("/cart/")

    if quantity <= 0:
        _, error = _service_request("DELETE", f"{CART_SERVICE_URL}/cart-items/{item_id}/")
        if error:
            messages.error(request, error)
    else:
        _, error = _service_request(
            "PUT",
            f"{CART_SERVICE_URL}/cart-items/{item_id}/",
            payload={"quantity": quantity},
        )
        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Đã cập nhật giỏ hàng.")

    return redirect("/cart/")


def remove_cart_item(request, product_id):
    if request.method != "POST":
        return redirect("/cart/")

    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    customer_id = _resolve_customer_id(request)
    cart_payload, cart_warnings = _fetch_remote_cart(customer_id)
    if cart_warnings:
        messages.error(request, cart_warnings[0])
        return redirect("/cart/")

    item_id = 0
    for row in cart_payload.get("items", []):
        if _to_int(row.get("product_id"), 0) == product_id:
            item_id = _to_int(row.get("id"), 0)
            break

    if item_id <= 0:
        messages.error(request, "Không tìm thấy sản phẩm trong giỏ hàng.")
        return redirect("/cart/")

    _, error = _service_request("DELETE", f"{CART_SERVICE_URL}/cart-items/{item_id}/")
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "Đã xóa sản phẩm khỏi giỏ hàng.")

    return redirect("/cart/")


def cart_view(request):
    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    customer_id = _resolve_customer_id(request, request.GET.get("customer_id"))
    products, warnings = _fetch_all_products()
    cart_payload, cart_warnings = _fetch_remote_cart(customer_id)
    items, total, total_quantity = _build_cart_items(products, cart_payload)

    context = {
        "items": items,
        "total": total,
        "total_quantity": total_quantity,
        "service_warnings": warnings + cart_warnings,
        "customer_id": customer_id,
    }
    context.update(_base_context(request, customer_id=customer_id, cart_count=total_quantity))
    return render(request, "cart.html", context)


def checkout_view(request):
    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    selected_customer_id = _to_int(request.GET.get("customer_id"), 0)
    selected_customer_id = _resolve_customer_id(request, selected_customer_id)

    products, warnings = _fetch_all_products()
    cart_payload, cart_warnings = _fetch_remote_cart(selected_customer_id)
    items, total, total_quantity = _build_cart_items(products, cart_payload)

    customers, customer_error = _fetch_customers()

    if not customers:
        customers = [
            {
                "id": 0,
                "name": "Khách lẻ",
                "email": "guest@example.com",
            }
        ]
        if customer_error:
            warnings.append(customer_error)
        else:
            warnings.append("Danh sách khách hàng đang trống. Hệ thống dùng chế độ thanh toán khách lẻ.")

    customer_ids = {_to_int(customer.get("id"), -1) for customer in customers if isinstance(customer, dict)}
    if selected_customer_id not in customer_ids and customers:
        selected_customer_id = _to_int(customers[0].get("id"), 0)
        _resolve_customer_id(request, selected_customer_id)

    if customer_error:
        warnings.append(customer_error)

    context = {
        "items": items,
        "total": total,
        "total_quantity": total_quantity,
        "customers": customers,
        "selected_customer_id": selected_customer_id,
        "service_warnings": warnings + cart_warnings,
    }
    context.update(_base_context(request, customer_id=selected_customer_id, cart_count=total_quantity))
    return render(request, "checkout.html", context)


def create_order(request):
    if request.method != "POST":
        return redirect("/checkout/")

    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    customer_id = _resolve_customer_id(request, request.POST.get("customer_id"))

    products, _ = _fetch_all_products()
    cart_payload, cart_warnings = _fetch_remote_cart(customer_id)
    if cart_warnings:
        messages.error(request, cart_warnings[0])
        return redirect("/checkout/")

    items, total, _ = _build_cart_items(products, cart_payload)
    if not items:
        messages.error(request, "Giỏ hàng đang trống.")
        return redirect("/cart/")

    payload = {
        "customer_id": customer_id,
        "total_amount": total,
        "payment_method": request.POST.get("payment_method", "cod"),
        "shipping_method": request.POST.get("shipping_method", "standard"),
        "shipping_address": request.POST.get("shipping_address", ""),
        "items": [
            {
                "product_id": item["product_id"],
                "name": item["product"]["name"],
                "category": item["product"]["category_label"],
                "price": item["product"]["price"],
                "quantity": item["quantity"],
                "line_total": item["line_total"],
            }
            for item in items
        ],
    }

    response_data, error = _service_request("POST", f"{ORDER_SERVICE_URL}/orders/", payload=payload)
    if error or not isinstance(response_data, dict):
        messages.error(request, error or "Không thể tạo đơn hàng.")
        return redirect("/checkout/")

    _, clear_error = _service_request("DELETE", f"{CART_SERVICE_URL}/carts/{customer_id}/items/")
    if clear_error:
        messages.warning(request, f"Tạo đơn thành công nhưng xóa giỏ hàng thất bại: {clear_error}")

    order_id = _to_int(response_data.get("id"), 0)
    messages.success(request, f"Đặt hàng thành công. Mã đơn: #{order_id}.")
    return redirect("/orders/")


def orders_view(request):
    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    customer_id = _resolve_customer_id(request, request.GET.get("customer_id"))
    orders, orders_error = _fetch_customer_orders(customer_id)

    normalized_orders = []
    for order in orders:
        if not isinstance(order, dict):
            continue

        status_key = str(order.get("status") or "unknown").strip().lower()
        payment_key = str(order.get("payment_method") or "cod").strip().lower()
        shipping_key = str(order.get("shipping_method") or "standard").strip().lower()

        normalized_orders.append(
            {
                "id": order.get("id"),
                "customer_id": order.get("customer_id"),
                "created_at": order.get("created_at"),
                "total": order.get("total") or order.get("total_amount") or "0.00",
                "status": _readable_label(status_key, ORDER_STATUS_LABELS, "Chưa cập nhật"),
                "payment_method": _readable_label(payment_key, PAYMENT_METHOD_LABELS, "Chưa cập nhật"),
                "shipping_method": _readable_label(shipping_key, SHIPPING_METHOD_LABELS, "Chưa cập nhật"),
                "shipping_address": order.get("shipping_address") or "",
                "items": order.get("items") if isinstance(order.get("items"), list) else [],
            }
        )

    context = {
        "orders": normalized_orders,
        "service_warnings": [orders_error] if orders_error else [],
        "customer_id": customer_id,
    }
    context.update(_base_context(request, customer_id=customer_id))
    return render(request, "orders.html", context)


def recommendations_view(request):
    redirect_response = _auth_required_redirect(request)
    if redirect_response:
        return redirect_response

    customer_id = _resolve_customer_id(request, request.GET.get("customer_id"))
    products, warnings = _fetch_all_products()
    favorite_ids = set(_get_favorite_ids(request))

    orders, orders_error = _fetch_customer_orders(customer_id)
    if orders_error:
        warnings.append(orders_error)

    reviews_data, reviews_error = _service_request(
        "GET",
        f"{COMMENT_RATE_SERVICE_URL}/reviews/",
        params={"customer_id": customer_id},
    )
    if reviews_error:
        warnings.append(reviews_error)

    if not isinstance(reviews_data, list):
        reviews_data = []

    score_by_category = {
        "laptop": 0,
        "mobile": 0,
    }

    for favorite_id in favorite_ids:
        category, _ = _decode_product_id(favorite_id)
        if category in score_by_category:
            score_by_category[category] += 3

    for order in orders:
        if not isinstance(order, dict):
            continue
        for item in order.get("items", []):
            if not isinstance(item, dict):
                continue
            category_label = (item.get("category") or "").lower()
            if category_label == "laptop":
                score_by_category["laptop"] += 1
            if category_label == "mobile":
                score_by_category["mobile"] += 1

    for review in reviews_data:
        if not isinstance(review, dict):
            continue
        rating = _to_int(review.get("rating"), 0)
        product_id = _to_int(review.get("product_id"), 0)
        category, _ = _decode_product_id(product_id)
        if category in score_by_category:
            score_by_category[category] += max(rating, 0)

    if score_by_category["laptop"] == 0 and score_by_category["mobile"] == 0:
        score_by_category["laptop"] = 1
        score_by_category["mobile"] = 1

    recommended = sorted(
        products,
        key=lambda product: (
            score_by_category.get(product["category"], 0),
            product["stock"],
            product["price_value"],
        ),
        reverse=True,
    )

    context = {
        "recommended_products": recommended[:8],
        "service_warnings": warnings,
        "customer_id": customer_id,
    }
    context.update(_base_context(request, customer_id=customer_id))
    return render(request, "recommendations.html", context)
