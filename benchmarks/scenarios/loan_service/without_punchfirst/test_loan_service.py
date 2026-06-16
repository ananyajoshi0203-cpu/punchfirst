# without_punchfirst/test_loan_service.py
#
# Tests written after the implementation, by the same author who wrote the code.
# Tests cover what the author remembered, not what the spec requires.
# Run: pytest without_punchfirst/ -v --tb=short

import pytest

from .loan_service import apply_prepayment, calculate_emi, calculate_late_fee, generate_amortization_schedule


# calculate_total


def test_calculate_emi_standard_loan():
    # 5,00,000 at 10.5% for 24 months
    emi = calculate_emi(500_000, 10.5, 24)
    assert emi == pytest.approx(23_188.02, abs=0.02)


def test_calculate_emi_small_loan():
    emi = calculate_emi(10_000, 12.0, 12)
    assert emi == pytest.approx(888.49, abs=1)


def test_calculate_emi_long_tenure():
    emi = calculate_emi(3_000_000, 8.5, 240)
    assert emi > 0


# generate_amortization_schedule


def test_schedule_has_correct_length():
    schedule = generate_amortization_schedule(100_000, 10.0, 12)
    assert len(schedule) == 12


def test_schedule_first_opening_balance():
    schedule = generate_amortization_schedule(100_000, 10.0, 12)
    assert schedule[0]["opening_balance"] == 100_000


def test_schedule_balances_decrease():
    schedule = generate_amortization_schedule(100_000, 10.0, 12)
    balances = [m["closing_balance"] for m in schedule]
    assert balances == sorted(balances, reverse=True)


# apply_prepayment


def test_prepayment_reduces_tenure():
    result = apply_prepayment(500_000, 10.5, 24, prepayment_month=6, prepayment_amount=100_000)
    assert result["new_tenure"] < result["original_tenure"]


def test_prepayment_saves_interest():
    result = apply_prepayment(500_000, 10.5, 24, prepayment_month=6, prepayment_amount=100_000)
    assert result["interest_saved"] > 0


# calculate_late_fee


def test_late_fee_zero_days():
    assert calculate_late_fee(5000, 0) == 0.0


def test_late_fee_positive_for_overdue():
    fee = calculate_late_fee(5000, 30)
    assert fee > 0


def test_late_fee_increases_with_days():
    fee_30 = calculate_late_fee(5000, 30)
    fee_60 = calculate_late_fee(5000, 60)
    assert fee_60 > fee_30


# Gaps: what was not tested (all caught in RED phase with punchfirst)
#
# calculate_emi:
#   principal <= 0      -> returns negative EMI, no error
#   tenure_months = 0   -> ZeroDivisionError
#   annual_rate = 0     -> ZeroDivisionError
#   tenure_months > 360 -> accepted silently
#   annual_rate > 100   -> accepted silently
#
# generate_amortization_schedule:
#   last closing_balance != 0.0 (rounding drift)
#   sum(principal_paid) != original principal
#
# apply_prepayment:
#   prepayment_amount > outstanding_balance -> wrong result, no error
#   prepayment_month = 0  -> IndexError crash
#   prepayment_month = tenure_months -> nonsensical, no error
#   new_schedule is always [] (empty)
#   interest_saved is an approximation
#
# calculate_late_fee:
#   emi_amount <= 0    -> returns negative fee
#   days_overdue < 0   -> returns negative fee
#   RBI cap not tested -> high penalty rate + long overdue exceeds 2x EMI silently
#   penalty_rate > 5%  -> accepted silently
