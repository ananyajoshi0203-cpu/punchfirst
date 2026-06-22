# without_punchfirst/order_service.py
#
# Simulates the typical "code first, tests after" workflow.
# Implementation written before any tests. Tests added once the code "works."


def calculate_total(items):
    # BUG-1: items=None crashes with AttributeError instead of raising ValueError
    # BUG-2: items=[] returns 0.0 silently; spec requires ValueError
    # BUG-3: negative price accepted; silently returns negative total
    # BUG-4: qty < 1 accepted silently; no validation
    # BUG-5: missing "price" or "qty" key raises KeyError, not ValueError
    total = 0
    for item in items:
        total += item["price"] * item["qty"]
    return round(total, 2)


def apply_discount(total, discount_code):
    # BUG-6: total=0 silently applies discount; spec requires ValueError
    # BUG-7: total<0 silently applies discount; spec requires ValueError
    if discount_code == "SAVE10":
        return round(total * 0.90, 2)
    elif discount_code == "SAVE20":
        return round(total * 0.80, 2)
    elif discount_code == "FREESHIP":
        return round(total, 2)
    else:
        raise ValueError(f"Unknown discount code: {discount_code}")


def validate_order(order):
    # BUG-8: order=None crashes with AttributeError; spec requires ValueError
    # BUG-9: missing "items" key returns False; spec requires ValueError with a message
    # BUG-10: empty items list returns False; spec requires ValueError with a message
    # BUG-11: missing "customer_email" key returns False silently; spec requires ValueError
    if not order.get("items"):
        return False
    if "@" not in order.get("customer_email", ""):
        return False
    return True
