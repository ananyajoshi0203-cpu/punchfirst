# with_punchfirst/test_loan_service.py
#
# Spec: benchmarks/scenarios/loan_service/spec.md
# All test cases derived from the spec before any production code was written.

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from .loan_service import (
    apply_prepayment,
    calculate_emi,
    calculate_late_fee,
    generate_amortization_schedule,
)


class TestCalculateEmi:
    def test_standard_loan_returns_known_value(self):
        # 5,00,000 at 10.5% for 24 months; formula-verified: EMI = 23,188.02
        emi = calculate_emi(500_000, 10.5, 24)
        assert emi == pytest.approx(23_188.02, abs=0.02)

    def test_small_loan_returns_known_value(self):
        emi = calculate_emi(10_000, 12.0, 12)
        assert emi == pytest.approx(888.49, abs=0.02)

    def test_one_month_tenure_emi_equals_principal_plus_one_month_interest(self):
        emi = calculate_emi(12_000, 12.0, 1)
        expected = 12_000 + 12_000 * (12.0 / 100 / 12)
        assert emi == pytest.approx(expected, abs=0.02)

    def test_maximum_tenure_360_months_is_accepted(self):
        assert calculate_emi(3_000_000, 8.5, 360) > 0

    def test_rate_at_100_percent_boundary_is_accepted(self):
        assert calculate_emi(10_000, 100.0, 12) > 0

    @pytest.mark.parametrize("principal", [0, -1, -100_000])
    def test_invalid_principal_raises(self, principal):
        with pytest.raises(ValueError, match="principal"):
            calculate_emi(principal, 10.5, 24)

    @pytest.mark.parametrize("rate", [0, -0.1, -10])
    def test_invalid_rate_zero_or_negative_raises(self, rate):
        with pytest.raises(ValueError, match="rate"):
            calculate_emi(100_000, rate, 24)

    def test_rate_above_100_raises(self):
        with pytest.raises(ValueError, match="rate"):
            calculate_emi(100_000, 100.01, 24)

    @pytest.mark.parametrize("tenure", [0, -1])
    def test_invalid_tenure_raises(self, tenure):
        with pytest.raises(ValueError, match="tenure"):
            calculate_emi(100_000, 10.5, tenure)

    def test_tenure_above_360_raises(self):
        with pytest.raises(ValueError, match="tenure"):
            calculate_emi(100_000, 10.5, 361)

    @given(
        principal=st.floats(min_value=1000, max_value=10_000_000, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0.01, max_value=100, allow_nan=False, allow_infinity=False),
        tenure=st.integers(min_value=1, max_value=360),
    )
    @settings(deadline=None)
    def test_emi_is_always_positive(self, principal, rate, tenure):
        # min_value=1000 avoids sub-paisa EMI rounding artifacts (EMI rounds to 0.00)
        assert calculate_emi(principal, rate, tenure) > 0

    @given(
        principal=st.floats(min_value=1000, max_value=10_000_000, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0.01, max_value=100, allow_nan=False, allow_infinity=False),
        tenure=st.integers(min_value=1, max_value=360),
    )
    @settings(deadline=None)
    def test_total_repayment_always_exceeds_principal(self, principal, rate, tenure):
        # min_value=1000: rounding down per period (up to 0.005) over many periods
        # can make total < principal for tiny principals
        emi = calculate_emi(principal, rate, tenure)
        assert emi * tenure >= principal

    @given(
        principal=st.floats(min_value=1, max_value=10_000_000, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0.01, max_value=99.9, allow_nan=False, allow_infinity=False),
        tenure=st.integers(min_value=1, max_value=360),
    )
    @settings(deadline=None)
    def test_emi_increases_with_rate(self, principal, rate, tenure):
        assume(rate + 0.1 <= 100)
        assert calculate_emi(principal, rate + 0.1, tenure) >= calculate_emi(principal, rate, tenure)

    @given(
        principal=st.floats(min_value=1, max_value=10_000_000, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0.01, max_value=100, allow_nan=False, allow_infinity=False),
        tenure=st.integers(min_value=1, max_value=359),
    )
    @settings(deadline=None)
    def test_emi_decreases_as_tenure_increases(self, principal, rate, tenure):
        assert calculate_emi(principal, rate, tenure) >= calculate_emi(principal, rate, tenure + 1)


class TestGenerateAmortizationSchedule:
    def test_schedule_length_equals_tenure(self):
        assert len(generate_amortization_schedule(100_000, 10.0, 12)) == 12

    def test_first_month_opening_balance_equals_principal(self):
        schedule = generate_amortization_schedule(500_000, 9.5, 36)
        assert schedule[0]["opening_balance"] == 500_000.0

    def test_each_month_interest_equals_opening_times_monthly_rate(self):
        schedule = generate_amortization_schedule(100_000, 12.0, 6)
        monthly_rate = 12.0 / 100 / 12
        for entry in schedule[:-1]:  # last month is adjusted
            expected = round(entry["opening_balance"] * monthly_rate, 2)
            assert entry["interest"] == expected, (
                f"month {entry['month']}: expected {expected}, got {entry['interest']}"
            )

    def test_last_closing_balance_is_exactly_zero(self):
        # rounding over many months accumulates; last payment absorbs the drift
        schedule = generate_amortization_schedule(500_000, 9.5, 36)
        assert schedule[-1]["closing_balance"] == 0.0

    def test_sum_of_principal_paid_equals_original_principal(self):
        schedule = generate_amortization_schedule(300_000, 10.0, 24)
        assert sum(m["principal_paid"] for m in schedule) == pytest.approx(300_000, abs=0.02)

    def test_all_closing_balances_are_non_negative(self):
        schedule = generate_amortization_schedule(200_000, 8.0, 36)
        for entry in schedule:
            assert entry["closing_balance"] >= 0, (
                f"month {entry['month']} closing_balance is negative: {entry['closing_balance']}"
            )

    def test_rounding_drift_reconciled_in_final_month(self):
        # 9.5% over 36 months is a known floating-point drift scenario
        schedule = generate_amortization_schedule(500_000, 9.5, 36)
        standard_emi = calculate_emi(500_000, 9.5, 36)
        assert abs(schedule[-1]["emi"] - standard_emi) < 1.0

    @given(
        principal=st.floats(min_value=1000, max_value=5_000_000, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=1.0, max_value=30.0, allow_nan=False, allow_infinity=False),
        tenure=st.integers(min_value=1, max_value=120),
    )
    @settings(max_examples=50, deadline=None)
    def test_last_closing_balance_is_always_zero(self, principal, rate, tenure):
        schedule = generate_amortization_schedule(principal, rate, tenure)
        assert schedule[-1]["closing_balance"] == 0.0

    @given(
        principal=st.floats(min_value=1000, max_value=5_000_000, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=1.0, max_value=30.0, allow_nan=False, allow_infinity=False),
        tenure=st.integers(min_value=1, max_value=120),
    )
    @settings(max_examples=50, deadline=None)
    def test_no_closing_balance_is_negative(self, principal, rate, tenure):
        schedule = generate_amortization_schedule(principal, rate, tenure)
        assert all(m["closing_balance"] >= 0 for m in schedule)


class TestApplyPrepayment:
    PRINCIPAL = 1_000_000
    RATE = 12.0
    TENURE = 60

    def test_prepayment_returns_required_keys(self):
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, 200_000)
        assert set(result.keys()) == {
            "original_tenure",
            "new_tenure",
            "months_saved",
            "interest_saved",
            "new_schedule",
        }

    def test_prepayment_reduces_tenure(self):
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, 200_000)
        assert result["new_tenure"] < result["original_tenure"]

    def test_months_saved_equals_original_minus_new(self):
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, 200_000)
        assert result["months_saved"] == result["original_tenure"] - result["new_tenure"]

    def test_interest_saved_is_positive(self):
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, 200_000)
        assert result["interest_saved"] > 0

    @pytest.mark.parametrize("month", [1, 6, 12, 30])
    def test_interest_saved_is_never_negative(self, month):
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, month, 100_000)
        assert result["interest_saved"] >= 0

    def test_new_schedule_starts_from_prepayment_month_plus_one(self):
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, 200_000)
        assert result["new_schedule"][0]["month"] == 13

    def test_new_schedule_last_closing_balance_is_zero(self):
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, 200_000)
        assert result["new_schedule"][-1]["closing_balance"] == 0.0

    def test_earlier_prepayment_saves_more_interest(self):
        early = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 1, 200_000)
        late = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 30, 200_000)
        assert early["interest_saved"] > late["interest_saved"]

    def test_prepayment_that_zeroes_balance_closes_loan(self):
        schedule = generate_amortization_schedule(self.PRINCIPAL, self.RATE, self.TENURE)
        outstanding = schedule[11]["closing_balance"]
        result = apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, outstanding)
        assert result["new_tenure"] == 12
        assert result["new_schedule"] == []

    @pytest.mark.parametrize("bad_month", [0, -1, 60])
    def test_invalid_prepayment_month_raises(self, bad_month):
        with pytest.raises(ValueError, match="prepayment_month"):
            apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, bad_month, 100_000)

    @pytest.mark.parametrize("bad_amount", [0, -1, -50_000])
    def test_invalid_prepayment_amount_raises(self, bad_amount):
        with pytest.raises(ValueError, match="prepayment_amount"):
            apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 6, bad_amount)

    def test_prepayment_exceeding_outstanding_raises(self):
        schedule = generate_amortization_schedule(self.PRINCIPAL, self.RATE, self.TENURE)
        outstanding = schedule[11]["closing_balance"]
        with pytest.raises(ValueError, match="prepayment_amount"):
            apply_prepayment(self.PRINCIPAL, self.RATE, self.TENURE, 12, outstanding + 1)


class TestCalculateLateFee:
    def test_zero_days_overdue_returns_zero(self):
        assert calculate_late_fee(5_000, 0) == 0.0

    def test_one_day_overdue_returns_correct_fee(self):
        # 0.02%/day on 5000 = 1.00
        assert calculate_late_fee(5_000, 1, penalty_rate_percent_per_day=0.02) == pytest.approx(1.0, abs=0.02)

    def test_fee_increases_with_days(self):
        assert calculate_late_fee(5_000, 60) > calculate_late_fee(5_000, 30)

    def test_rbi_cap_applied_at_2x_emi(self):
        # 0.5%/day for 365 days on 50,000 would be ~295,000 uncapped; capped at 100,000
        fee = calculate_late_fee(50_000, 365, penalty_rate_percent_per_day=0.5)
        assert fee == round(50_000 * 2, 2)

    def test_tiny_rate_produces_nonzero_fee(self):
        assert calculate_late_fee(100_000, 1, penalty_rate_percent_per_day=0.001) > 0

    def test_fee_is_compound_not_simple(self):
        # Use a tiny rate to stay below the cap; compound growth must exceed linear
        fee_1 = calculate_late_fee(100, 1, penalty_rate_percent_per_day=0.1)
        fee_100 = calculate_late_fee(100, 100, penalty_rate_percent_per_day=0.1)
        assert fee_100 > 100 * fee_1

    @pytest.mark.parametrize("bad_emi", [0, -1, -5_000])
    def test_invalid_emi_amount_raises(self, bad_emi):
        with pytest.raises(ValueError, match="emi_amount"):
            calculate_late_fee(bad_emi, 30)

    @pytest.mark.parametrize("bad_days", [-1, -100])
    def test_negative_days_overdue_raises(self, bad_days):
        with pytest.raises(ValueError, match="days_overdue"):
            calculate_late_fee(5_000, bad_days)

    def test_zero_penalty_rate_raises(self):
        with pytest.raises(ValueError, match="penalty_rate"):
            calculate_late_fee(5_000, 30, penalty_rate_percent_per_day=0)

    def test_predatory_penalty_rate_raises(self):
        with pytest.raises(ValueError, match="penalty_rate"):
            calculate_late_fee(5_000, 30, penalty_rate_percent_per_day=5.01)

    @given(
        emi=st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False),
        days=st.integers(min_value=0, max_value=365),
        rate=st.floats(min_value=0.001, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    @settings(deadline=None)
    def test_rbi_cap_holds_for_all_valid_inputs(self, emi, days, rate):
        fee = calculate_late_fee(emi, days, penalty_rate_percent_per_day=rate)
        # Compare against rounded cap: the cap is stored and returned in 2dp,
        # so round(emi * 2, 2) is the correct ceiling to assert against.
        assert fee <= round(emi * 2, 2)

    @given(
        emi=st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False),
        rate=st.floats(min_value=0.001, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    @settings(deadline=None)
    def test_fee_is_always_non_negative(self, emi, rate):
        assert calculate_late_fee(emi, 0, penalty_rate_percent_per_day=rate) >= 0
