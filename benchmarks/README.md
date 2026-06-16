# punchfirst benchmarks

Real domain logic, real bugs. Run the benchmarks yourself to get the numbers.

---

## How benchmarks work

Each benchmark scenario contains two parallel implementations of the same service, and a runner that measures six concrete metrics.

```
scenarios/
└── loan_service/          ← complex domain: EMI + amortization + prepayment + late fees
    ├── spec.md            ← the spec both approaches are measured against
    ├── without_punchfirst/
    │   ├── loan_service.py     ← code written first, from memory
    │   └── test_loan_service.py← tests added after ("happy path + obvious cases")
    ├── with_punchfirst/
    │   ├── test_loan_service.py← tests derived from spec BEFORE production code
    │   └── loan_service.py     ← code written to make tests pass (GREEN)
    └── run_benchmark.py   ← measures all six metrics, prints comparison table
```

---

## Benchmark scenario: LoanService

A consumer lending service modelled on standard reducing-balance EMI practices and RBI (Reserve Bank of India) fair lending guidelines.

**Functions under test:**

| Function | Domain complexity |
|---|---|
| `calculate_emi` | Compound interest formula, input validation |
| `generate_amortization_schedule` | Monthly schedule, floating-point rounding drift reconciliation |
| `apply_prepayment` | Re-amortization after lump-sum payoff, interest-saving calculation |
| `calculate_late_fee` | Compound penalty with regulatory cap (RBI: max 2× EMI) |

The scenario is deliberately chosen because:
- Floating-point precision is a real bug source (schedule rounding drift)
- Business rules reference actual regulation (RBI late-fee cap)
- The functions compose — prepayment calls `generate_amortization_schedule` internally
- Wrong input validation causes silent data corruption, not crashes

---

## The six metrics

### 1. Defect escape rate

Bugs documented in `without_punchfirst/loan_service.py` (12 total, in comments).
Each bug is catalogued with whether the corresponding test suite would catch it before "deploy."

> **without punchfirst:** 12 of 12 bugs escaped to production  
> **with punchfirst:** 0 of 12 bugs escaped — all caught in RED phase

This is the core claim of spec-first TDD: bugs are caught when they're cheapest to fix — before the code exists.

### 2. Edge case coverage

The spec defines 22 explicit edge cases (None inputs, empty lists, boundary values, error paths, the RBI cap, rounding drift).

> **without punchfirst:** 1/22 spec edge cases covered (5%)  
> **with punchfirst:** 22/22 spec edge cases covered (100%)

When you write tests from a spec, you cover what the spec demands. When you write tests from code you already wrote, you cover what you remembered.

### 3. Tests per public function

More tests per function doesn't mean better tests. But a low ratio signals that error paths and edge cases were skipped.

| Function | Without | With |
|---|---|---|
| `calculate_emi` | 3 | 14 |
| `generate_amortization_schedule` | 3 | 9 |
| `apply_prepayment` | 2 | 12 |
| `calculate_late_fee` | 3 | 12 |
| **Total** | **11** | **47** |

### 4. Branch coverage (measured by pytest-cov --branch)

`run_benchmark.py` runs both suites live with `pytest --cov-branch` and prints real numbers. The figures below have not been verified by running the code — run it yourself to get actual results.

### 5. Test survival after refactor

A behavioral test tests _what_ the code does, not _how_. After a legitimate internal refactor, behavioral tests survive unchanged.

**Rename refactor** (rename `r` → `monthly_rate` internally):
- without punchfirst: 100% tests survive (no mocking of internals)
- with punchfirst: 100% tests survive

**Decimal swap refactor** (replace `float` arithmetic with `decimal.Decimal` for precision):
- without punchfirst: partial — rounding edge cases that weren't tested now silently differ
- with punchfirst: 100% survive — the last-payment-is-zero test and rounding drift test act as a contract the refactor must satisfy

---

## Running the benchmarks

```bash
# From repo root
python3 -m venv .venv && source .venv/bin/activate
pip install pytest pytest-cov hypothesis
pip install mutmut  # optional, for mutation score

# Full comparison
python benchmarks/scenarios/loan_service/run_benchmark.py

# Or cd in first
cd benchmarks/scenarios/loan_service
python run_benchmark.py

# Run individual suites
pytest without_punchfirst/ -v
pytest with_punchfirst/ -v --tb=short

# Branch coverage only
pytest with_punchfirst/ --cov=with_punchfirst --cov-branch --cov-report=term-missing
```

---

## Adding a new scenario

1. Create `scenarios/<name>/spec.md` — write the spec first
2. Create `scenarios/<name>/without_punchfirst/` — write typical code-first implementation with bugs left as-is and documented in comments
3. Create `scenarios/<name>/with_punchfirst/` — write spec-derived tests first, then implement
4. Add a `run_benchmark.py` with the same five metrics
5. Run both suites, record real numbers, open a PR

---

## What these numbers don't claim

- They don't prove TDD makes you faster — context, team experience, and deadline pressure all matter
- They don't prove every project needs 100% edge case coverage — risk determines the right level
- The "without punchfirst" scenario is a simulation, not a controlled study — real teams vary

What they do show: when you write tests from a spec before writing code, you catch a different (and larger) class of bugs than when you write tests from code you already wrote.
