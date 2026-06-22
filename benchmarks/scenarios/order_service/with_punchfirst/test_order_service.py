# with_punchfirst/test_order_service.py
#
# Spec: benchmarks/scenarios/order_service/spec.md
# All test cases derived from the spec before any production code was written.

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from .order_service import apply_discount, calculate_total, validate_order


def _item(price=10.0, qty=1, name="Widget"):
    return {"name": name, "price": price, "qty": qty}


class TestCalculateTotal:
    def test_single_item(self):
        assert calculate_total([_item(price=9.99, qty=1)]) == 9.99

    def test_multiple_items(self):
        items = [_item(price=10.0, qty=2), _item(price=5.0, qty=3)]
        assert calculate_total(items) == 35.0

    def test_large_qty(self):
        assert calculate_total([_item(price=1.0, qty=10_000)]) == 10_000.0

    def test_qty_one_boundary(self):
        assert calculate_total([_item(price=5.0, qty=1)]) == 5.0

    def test_float_price_accumulation(self):
        # 0.1 * 10 repeated — classic float drift scenario from the spec
        items = [_item(price=0.1, qty=10)] * 3
        assert calculate_total(items) == pytest.approx(3.0, abs=0.001)

    def test_result_has_at_most_two_decimal_places(self):
        items = [_item(price=1 / 3, qty=1)] * 3
        result = calculate_total(items)
        assert result == round(result, 2)

    def test_none_raises(self):
        with pytest.raises(ValueError):
            calculate_total(None)

    def test_empty_list_raises(self):
        with pytest.raises(ValueError):
            calculate_total([])

    @pytest.mark.parametrize("price", [-0.01, -10.0, -999.0])
    def test_negative_price_raises(self, price):
        with pytest.raises(ValueError, match="price"):
            calculate_total([_item(price=price)])

    @pytest.mark.parametrize("qty", [0, -1, -50])
    def test_qty_less_than_one_raises(self, qty):
        with pytest.raises(ValueError, match="qty"):
            calculate_total([_item(qty=qty)])

    def test_missing_price_key_raises(self):
        with pytest.raises(ValueError, match="price"):
            calculate_total([{"name": "Widget", "qty": 2}])

    def test_missing_qty_key_raises(self):
        with pytest.raises(ValueError, match="qty"):
            calculate_total([{"name": "Widget", "price": 5.0}])

    def test_invalid_item_in_mixed_list_raises(self):
        items = [_item(price=10.0, qty=2), {"name": "Bad", "price": -1.0, "qty": 1}]
        with pytest.raises(ValueError, match="price"):
            calculate_total(items)

    @given(
        prices=st.lists(
            st.floats(min_value=0.01, max_value=10_000, allow_nan=False, allow_infinity=False),
            min_size=1, max_size=20,
        ),
        qtys=st.lists(
            st.integers(min_value=1, max_value=1_000),
            min_size=1, max_size=20,
        ),
    )
    @settings(deadline=None)
    def test_total_is_always_non_negative(self, prices, qtys):
        items = [_item(price=p, qty=q) for p, q in zip(prices, qtys)]
        assert calculate_total(items) >= 0


class TestApplyDiscount:
    def test_save10_reduces_by_10_percent(self):
        assert apply_discount(200.0, "SAVE10") == 180.0

    def test_save20_reduces_by_20_percent(self):
        assert apply_discount(200.0, "SAVE20") == 160.0

    def test_freeship_leaves_total_unchanged(self):
        assert apply_discount(99.99, "FREESHIP") == 99.99

    def test_unknown_code_raises(self):
        with pytest.raises(ValueError, match="unknown"):
            apply_discount(100.0, "HALFOFF")

    @pytest.mark.parametrize("total", [0, -0.01, -50.0])
    def test_zero_or_negative_total_raises(self, total):
        with pytest.raises(ValueError):
            apply_discount(total, "SAVE10")

    def test_result_rounded_to_two_dp(self):
        # 33.33 * 0.9 = 29.997 → rounds to 30.0
        result = apply_discount(33.33, "SAVE10")
        assert result == round(result, 2)

    def test_save20_compounds_correctly_on_odd_amount(self):
        # Verify it's 80% of total, not two rounds of 10%
        assert apply_discount(150.0, "SAVE20") == 120.0

    @given(total=st.floats(min_value=0.01, max_value=100_000, allow_nan=False, allow_infinity=False))
    @settings(deadline=None)
    def test_discount_never_increases_total(self, total):
        # compare against round(total, 2) — the function works in 2dp space,
        # so FREESHIP can round up a raw float like 1.109375 → 1.11
        for code in ("SAVE10", "SAVE20", "FREESHIP"):
            assert apply_discount(total, code) <= round(total, 2)

    @given(total=st.floats(min_value=0.01, max_value=100_000, allow_nan=False, allow_infinity=False))
    @settings(deadline=None)
    def test_freeship_always_preserves_total(self, total):
        assert apply_discount(total, "FREESHIP") == round(total, 2)


class TestValidateOrder:
    def test_valid_order_returns_true(self, standard_order):
        assert validate_order(standard_order) is True

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_order(None)

    def test_missing_items_key_raises(self):
        with pytest.raises(ValueError, match="items"):
            validate_order({"customer_email": "a@b.com"})

    def test_missing_email_key_raises(self):
        with pytest.raises(ValueError, match="customer_email"):
            validate_order({"items": [_item()]})

    def test_empty_items_list_raises(self):
        with pytest.raises(ValueError, match="items"):
            validate_order({"items": [], "customer_email": "a@b.com"})

    def test_email_without_at_raises(self):
        with pytest.raises(ValueError, match="customer_email"):
            validate_order({"items": [_item()], "customer_email": "notanemail"})

    def test_empty_email_raises(self):
        with pytest.raises(ValueError, match="customer_email"):
            validate_order({"items": [_item()], "customer_email": ""})

    def test_error_messages_name_the_bad_field(self):
        # A generic "invalid order" message is useless in production logs.
        # The error must tell you which field is wrong.
        with pytest.raises(ValueError, match="items"):
            validate_order({"items": [], "customer_email": "a@b.com"})
        with pytest.raises(ValueError, match="customer_email"):
            validate_order({"items": [_item()], "customer_email": "bad"})
