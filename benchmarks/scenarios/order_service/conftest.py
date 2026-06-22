# conftest.py
#
# Shared fixtures for both suites.

import pytest


@pytest.fixture
def standard_order():
    """Typical two-item order — the common case."""
    return {
        "items": [
            {"name": "Widget", "price": 29.99, "qty": 2},
            {"name": "Gadget", "price": 9.99, "qty": 1},
        ],
        "customer_email": "aj@example.com",
    }


@pytest.fixture
def single_item_order():
    """One item, qty > 1. Used for total/discount round-trip checks."""
    return {
        "items": [{"name": "Pen", "price": 1.50, "qty": 4}],
        "customer_email": "user@test.com",
    }


@pytest.fixture
def high_value_order():
    """Large quantities — exercises float accumulation and rounding."""
    return {
        "items": [
            {"name": "Laptop", "price": 999.99, "qty": 10},
            {"name": "Bag", "price": 49.99, "qty": 10},
        ],
        "customer_email": "bulk@reseller.com",
    }
