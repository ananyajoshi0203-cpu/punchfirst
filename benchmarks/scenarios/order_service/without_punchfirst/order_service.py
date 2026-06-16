# without_punchfirst/order_service.py
#
# Simulates the typical "code first, tests after" workflow.
# Implementation written before any tests. Tests added once the code "works."


def calculate_total(items):
    total = 0
    for item in items:
        total += item["price"] * item["qty"]
    return round(total, 2)


def apply_discount(total, discount_code):
    if discount_code == "SAVE10":
        return round(total * 0.90, 2)
    elif discount_code == "SAVE20":
        return round(total * 0.80, 2)
    elif discount_code == "FREESHIP":
        return round(total, 2)
    else:
        raise ValueError(f"Unknown discount code: {discount_code}")


def validate_order(order):
    if not order.get("items"):
        return False
    if "@" not in order.get("customer_email", ""):
        return False
    return True
