# with_punchfirst/loan_service.py
#
# Step 5: minimum code to make all tests pass (GREEN).
# Written after test_loan_service.py. Every line exists because a test requires it.


def _validated_emi_inputs(
    principal: float, annual_rate_percent: float, tenure_months: int
) -> None:
    if principal <= 0:
        raise ValueError(f"principal must be > 0, got {principal!r}")
    if annual_rate_percent <= 0 or annual_rate_percent > 100:
        raise ValueError(
            f"annual_rate_percent must be in (0, 100], got {annual_rate_percent!r}"
        )
    if tenure_months < 1 or tenure_months > 360:
        raise ValueError(
            f"tenure_months must be in [1, 360], got {tenure_months!r}"
        )


def calculate_emi(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
) -> float:
    _validated_emi_inputs(principal, annual_rate_percent, tenure_months)
    r = annual_rate_percent / 100 / 12
    n = tenure_months
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return round(emi, 2)


def generate_amortization_schedule(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
) -> list[dict]:
    _validated_emi_inputs(principal, annual_rate_percent, tenure_months)
    emi = calculate_emi(principal, annual_rate_percent, tenure_months)
    r = annual_rate_percent / 100 / 12
    schedule = []
    balance = principal

    for month in range(1, tenure_months + 1):
        opening = round(balance, 2)
        interest = round(opening * r, 2)

        if month == tenure_months:
            # Last month: absorb all rounding drift so closing_balance is exactly 0.0
            principal_paid = opening
            actual_emi = round(opening + interest, 2)
            closing = 0.0
        else:
            principal_paid = round(emi - interest, 2)
            actual_emi = emi
            closing = round(opening - principal_paid, 2)

        schedule.append({
            "month": month,
            "opening_balance": opening,
            "emi": actual_emi,
            "interest": interest,
            "principal_paid": principal_paid,
            "closing_balance": closing,
        })
        balance = closing

    return schedule


def apply_prepayment(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
    prepayment_month: int,
    prepayment_amount: float,
) -> dict:
    _validated_emi_inputs(principal, annual_rate_percent, tenure_months)

    if prepayment_month < 1 or prepayment_month >= tenure_months:
        raise ValueError(
            f"prepayment_month must be in [1, {tenure_months - 1}], "
            f"got {prepayment_month!r}"
        )
    if prepayment_amount <= 0:
        raise ValueError(f"prepayment_amount must be > 0, got {prepayment_amount!r}")

    orig_schedule = generate_amortization_schedule(principal, annual_rate_percent, tenure_months)
    orig_interest = sum(m["interest"] for m in orig_schedule)
    outstanding = orig_schedule[prepayment_month - 1]["closing_balance"]

    if prepayment_amount > outstanding:
        raise ValueError(
            f"prepayment_amount ({prepayment_amount}) exceeds outstanding balance "
            f"({outstanding}) at month {prepayment_month}"
        )

    remaining_balance = round(outstanding - prepayment_amount, 2)

    if remaining_balance == 0.0:
        paid_interest = sum(m["interest"] for m in orig_schedule[:prepayment_month])
        return {
            "original_tenure": tenure_months,
            "new_tenure": prepayment_month,
            "months_saved": tenure_months - prepayment_month,
            "interest_saved": round(orig_interest - paid_interest, 2),
            "new_schedule": [],
        }

    original_emi = orig_schedule[0]["emi"]
    r = annual_rate_percent / 100 / 12
    new_tail = []
    balance = remaining_balance
    month_num = prepayment_month + 1
    max_months = tenure_months * 2

    while balance > 0 and len(new_tail) < max_months:
        opening = round(balance, 2)
        interest = round(opening * r, 2)

        if round(original_emi - interest, 2) >= opening:
            actual_emi = round(opening + interest, 2)
            new_tail.append({
                "month": month_num,
                "opening_balance": opening,
                "emi": actual_emi,
                "interest": interest,
                "principal_paid": opening,
                "closing_balance": 0.0,
            })
            balance = 0.0
        else:
            principal_paid = round(original_emi - interest, 2)
            closing = round(opening - principal_paid, 2)
            new_tail.append({
                "month": month_num,
                "opening_balance": opening,
                "emi": original_emi,
                "interest": interest,
                "principal_paid": principal_paid,
                "closing_balance": closing,
            })
            balance = closing

        month_num += 1

    new_tenure = prepayment_month + len(new_tail)
    new_interest = sum(m["interest"] for m in orig_schedule[:prepayment_month]) + sum(
        m["interest"] for m in new_tail
    )
    interest_saved = round(orig_interest - new_interest, 2)

    return {
        "original_tenure": tenure_months,
        "new_tenure": new_tenure,
        "months_saved": tenure_months - new_tenure,
        "interest_saved": max(0.0, interest_saved),
        "new_schedule": new_tail,
    }


def calculate_late_fee(
    emi_amount: float,
    days_overdue: int,
    penalty_rate_percent_per_day: float = 0.02,
) -> float:
    # RBI (Reserve Bank of India) fair lending guideline:
    # penalty interest on EMI defaults cannot exceed 2x the EMI amount.
    if emi_amount <= 0:
        raise ValueError(f"emi_amount must be > 0, got {emi_amount!r}")
    if days_overdue < 0:
        raise ValueError(f"days_overdue must be >= 0, got {days_overdue!r}")
    if penalty_rate_percent_per_day <= 0:
        raise ValueError(
            f"penalty_rate_percent_per_day must be > 0, got {penalty_rate_percent_per_day!r}"
        )
    if penalty_rate_percent_per_day > 5:
        raise ValueError(
            f"penalty_rate_percent_per_day > 5% per day is not permitted "
            f"(got {penalty_rate_percent_per_day!r})"
        )

    if days_overdue == 0:
        return 0.0

    rate = penalty_rate_percent_per_day / 100
    fee = emi_amount * ((1 + rate) ** days_overdue - 1)
    # Cap rounded to 2dp first; then take the min so rounding can't push fee over cap.
    cap = round(emi_amount * 2.0, 2)
    return min(round(fee, 2), cap)
