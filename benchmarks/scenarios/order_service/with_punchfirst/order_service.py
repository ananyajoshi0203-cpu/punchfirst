# with_punchfirst/order_service.py
#
# Step 5: minimum code to make all tests pass (GREEN).
# Written after test_order_service.py. Every line exists because a test requires it.

from __future__ import annotations

_DISCOUNT_RATES: dict[str, float] = {
    "SAVE10": 0.10,
    "SAVE20": 0.20,
    "FREESHIP": 0.0,
}


def calculate_total(items: list[dict]) -> float:
    if items is None:
        raise ValueError("items cannot be None")
    if not items:
        raise ValueError("items cannot be empty")
    for item in items:
        missing = [k for k in ("price", "qty") if k not in item]
        if missing:
            raise ValueError(f"item missing required keys: {missing!r}")
        if item["price"] < 0:
            raise ValueError(f"price cannot be negative, got {item['price']!r}")
        if item["qty"] < 1:
            raise ValueError(f"qty must be >= 1, got {item['qty']!r}")
    return round(sum(item["price"] * item["qty"] for item in items), 2)


def apply_discount(total: float, discount_code: str) -> float:
    if total <= 0:
        raise ValueError(f"total must be > 0, got {total!r}")
    if discount_code not in _DISCOUNT_RATES:
        raise ValueError(f"unknown discount code: {discount_code!r}")
    return round(total * (1 - _DISCOUNT_RATES[discount_code]), 2)


def validate_order(order: dict) -> bool:
    if order is None:
        raise ValueError("order cannot be None")
    if "items" not in order:
        raise ValueError("order is missing required field: 'items'")
    if "customer_email" not in order:
        raise ValueError("order is missing required field: 'customer_email'")
    if not order["items"]:
        raise ValueError("order['items'] cannot be empty")
    if not order["customer_email"] or "@" not in order["customer_email"]:
        raise ValueError(f"customer_email is not valid: {order['customer_email']!r}")
    return True
