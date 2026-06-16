# LoanService spec

A loan EMI calculator and amortization engine used in a consumer lending app.
Business rules are modelled on standard reducing-balance EMI lending practices.

---

## calculate_emi

```python
def calculate_emi(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
) -> float
```

**Formula:** EMI = P × r × (1 + r)^n / ((1 + r)^n − 1)
where `r = annual_rate_percent / 100 / 12`, `n = tenure_months`

**Behaviors:**
- Returns EMI rounded to 2 decimal places
- Raises `ValueError` if `principal <= 0`
- Raises `ValueError` if `annual_rate_percent <= 0`
- Raises `ValueError` if `annual_rate_percent > 100` (sanity guard)
- Raises `ValueError` if `tenure_months < 1`
- Raises `ValueError` if `tenure_months > 360` (30 years max)

**Edge cases:**
- Exact integer result (e.g. 1000 principal, 12%, 12 months — verify no rounding surprises)
- Very short tenure (1 month — EMI ≈ principal + one month's interest)
- Very long tenure (360 months)
- High rate near boundary (100%)

---

## generate_amortization_schedule

```python
def generate_amortization_schedule(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
) -> list[dict]
```

Each entry: `{"month": int, "opening_balance": float, "emi": float,
              "interest": float, "principal_paid": float, "closing_balance": float}`

**Behaviors:**
- Returns exactly `tenure_months` entries
- Month 1 `opening_balance` equals `principal`
- `interest = round(opening_balance * monthly_rate, 2)` for each month
- `principal_paid = emi - interest` for each month (except last)
- `closing_balance = opening_balance - principal_paid`
- **Last month:** `emi` adjusted so `closing_balance` is exactly `0.0` (absorbs rounding drift)
- Sum of all `principal_paid` equals original `principal` (within ±0.02 rounding tolerance)
- Raises same errors as `calculate_emi`

**Edge cases:**
- Single-month loan (1 entry, closing_balance must be 0)
- Rounding drift: 36-month loan at 9.5% — cumulative interest drift must not leave residual
- All `closing_balance` values must be ≥ 0

---

## apply_prepayment

```python
def apply_prepayment(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
    prepayment_month: int,
    prepayment_amount: float,
) -> dict
```

Returns:
```python
{
    "original_tenure": int,
    "new_tenure": int,
    "months_saved": int,
    "interest_saved": float,
    "new_schedule": list[dict],   # re-amortized from prepayment_month+1
}
```

**Behaviors:**
- Calculates schedule up to `prepayment_month`, applies prepayment to outstanding balance
- Re-amortizes remaining balance at the same rate and same original EMI
- `new_tenure` = months already paid + remaining months after prepayment
- `interest_saved` = total interest of original schedule − total interest of new schedule
- Raises `ValueError` if `prepayment_month < 1` or `prepayment_month >= tenure_months`
- Raises `ValueError` if `prepayment_amount <= 0`
- Raises `ValueError` if `prepayment_amount > outstanding_balance_at_month` (can't overpay)

**Edge cases:**
- Prepayment in month 1 (maximum interest saving)
- Prepayment in last available month (month `tenure_months - 1`)
- Prepayment that exactly zeroes remaining balance (loan fully closed)
- `interest_saved` must always be ≥ 0 (prepayment never increases total interest)

---

## calculate_late_fee

```python
def calculate_late_fee(
    emi_amount: float,
    days_overdue: int,
    penalty_rate_percent_per_day: float = 0.02,
) -> float
```

**Formula:** `fee = emi_amount × ((1 + rate/100)^days − 1)`, rounded to 2 decimal places

**Business rule (RBI-style cap):** Late fee cannot exceed `emi_amount × 2.0`

**Behaviors:**
- Returns 0.0 if `days_overdue == 0`
- Returns fee capped at `emi_amount * 2` if compound amount exceeds cap
- Raises `ValueError` if `emi_amount <= 0`
- Raises `ValueError` if `days_overdue < 0`
- Raises `ValueError` if `penalty_rate_percent_per_day <= 0`
- Raises `ValueError` if `penalty_rate_percent_per_day > 5` (sanity guard: >5% per day is predatory)

**Edge cases:**
- `days_overdue = 0` → fee is exactly `0.0`
- `days_overdue = 1` → fee = one day of compound interest
- Long overdue (365 days) → fee hits cap
- Tiny rate (0.001%) → fee should be a small positive number, not 0
