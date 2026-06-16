# without_punchfirst/loan_service.py
#
# Simulates code written first, tests added after.
# No spec was consulted during coding.
# This version has documented bugs that slipped through because
# tests were written from the code, not from the spec.


def calculate_emi(principal, annual_rate_percent, tenure_months):
    r = annual_rate_percent / 100 / 12
    n = tenure_months
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return round(emi, 2)
    # BUG-1: No input validation. principal=-100000 silently returns a negative EMI.
    # BUG-2: tenure_months=0 causes ZeroDivisionError with no helpful message.
    # BUG-3: annual_rate_percent=0 causes ZeroDivisionError.


def generate_amortization_schedule(principal, annual_rate_percent, tenure_months):
    emi = calculate_emi(principal, annual_rate_percent, tenure_months)
    r = annual_rate_percent / 100 / 12
    schedule = []
    balance = principal

    for month in range(1, tenure_months + 1):
        interest = round(balance * r, 2)
        principal_paid = round(emi - interest, 2)
        closing = round(balance - principal_paid, 2)
        schedule.append({
            "month": month,
            "opening_balance": round(balance, 2),
            "emi": emi,
            "interest": interest,
            "principal_paid": principal_paid,
            "closing_balance": closing,
        })
        balance = closing

    # BUG-4: Last payment not adjusted. closing_balance of the final month is
    # often -0.01 or 0.01 due to accumulated rounding; not exactly 0.0.
    return schedule


def apply_prepayment(
    principal, annual_rate_percent, tenure_months, prepayment_month, prepayment_amount
):
    schedule = generate_amortization_schedule(principal, annual_rate_percent, tenure_months)
    orig_interest = sum(m["interest"] for m in schedule)

    balance_after = schedule[prepayment_month - 1]["closing_balance"] - prepayment_amount

    original_emi = schedule[0]["emi"]
    r = annual_rate_percent / 100 / 12
    remaining_months = 0
    bal = balance_after
    while bal > 0 and remaining_months < tenure_months:
        interest = bal * r
        principal_paid = original_emi - interest
        if principal_paid <= 0:
            break
        bal -= principal_paid
        remaining_months += 1

    new_tenure = prepayment_month + remaining_months

    # BUG-5: No check for prepayment_amount > outstanding_balance.
    #   balance_after goes negative, loop exits, no error raised.
    # BUG-6: interest_saved is a rough approximation; no proper re-amortization.
    # BUG-7: prepayment_month=0 crashes with IndexError.
    # BUG-8: prepayment_month=tenure_months is accepted (nonsensical).

    new_interest = bal * r * remaining_months  # crude approximation
    interest_saved = round(orig_interest - new_interest, 2)

    return {
        "original_tenure": tenure_months,
        "new_tenure": new_tenure,
        "months_saved": tenure_months - new_tenure,
        "interest_saved": max(0, interest_saved),
        "new_schedule": [],  # BUG-9: always empty; caller gets no schedule data
    }


def calculate_late_fee(emi_amount, days_overdue, penalty_rate_percent_per_day=0.02):
    if days_overdue == 0:
        return 0.0
    rate = penalty_rate_percent_per_day / 100
    fee = emi_amount * ((1 + rate) ** days_overdue - 1)
    # BUG-10: RBI cap not applied. At 0.5%/day the fee explodes past 2x EMI.
    # BUG-11: emi_amount=-1 silently returns a negative fee.
    # BUG-12: days_overdue=-5 silently returns a negative fee.
    return round(fee, 2)
