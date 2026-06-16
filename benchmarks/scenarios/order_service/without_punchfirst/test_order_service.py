# without_punchfirst/test_order_service.py
#
# Tests written AFTER implementation. No spec consulted — tests reflect
# what the author remembered to check while looking at the code.
# Run: pytest without_punchfirst/test_order_service.py -v

import pytest
from .order_service import calculate_total, apply_discount, validate_order


# ── calculate_total ─────────────────────────────────────────────────────────

def test_calculate_total_basic():
    items = [{"name": "Widget", "price": 10.0, "qty": 2}]
    assert calculate_total(items) == 20.0


def test_calculate_total_multiple_items():
    items = [
        {"name": "Widget", "price": 10.0, "qty": 2},
        {"name": "Gadget", "price": 5.0, "qty": 3},
    ]
    assert calculate_total(items) == 35.0


def test_calculate_total_rounds():
    items = [{"name": "Pen", "price": 0.1, "qty": 3}]
    assert calculate_total(items) == 0.30


# ── apply_discount ───────────────────────────────────────────────────────────

def test_apply_discount_save10():
    assert apply_discount(100.0, "SAVE10") == 90.0


def test_apply_discount_save20():
    assert apply_discount(100.0, "SAVE20") == 80.0


def test_apply_discount_invalid_code():
    with pytest.raises(ValueError):
        apply_discount(100.0, "BOGUS")


# ── validate_order ───────────────────────────────────────────────────────────

def test_validate_order_valid():
    order = {
        "items": [{"name": "Widget", "price": 10.0, "qty": 1}],
        "customer_email": "test@example.com",
    }
    assert validate_order(order) is True


def test_validate_order_missing_email_at():
    order = {
        "items": [{"name": "Widget", "price": 10.0, "qty": 1}],
        "customer_email": "not-an-email",
    }
    assert validate_order(order) is False


# ── What was NOT tested (spec had these, author forgot) ──────────────────────
#
# calculate_total:
#   - items=None           → crashes with AttributeError (unhelpful error)
#   - items=[]             → returns 0.0 silently (wrong: spec says ValueError)
#   - negative price       → returns negative total silently (wrong)
#   - qty < 1              → no check, silently wrong
#   - missing "price" key  → crashes with KeyError (unhelpful error)
#
# apply_discount:
#   - total <= 0           → applies discount to 0 or negative total (wrong)
#   - FREESHIP             → not tested at all
#
# validate_order:
#   - order=None           → crashes with AttributeError (unhelpful error)
#   - missing "items" key  → returns False (spec says ValueError with message)
#   - empty items list     → returns False (spec says ValueError with message)
#
# All of these are real bugs that shipped. None were caught before deploy.
