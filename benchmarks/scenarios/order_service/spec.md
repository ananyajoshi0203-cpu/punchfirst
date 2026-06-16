# OrderService spec

A minimal e-commerce order processor.

## calculate_total

```python
def calculate_total(items: list[dict]) -> float
```

Each item dict: `{"name": str, "price": float, "qty": int}`

**Behaviors:**
- Returns `sum(price * qty)` for all items, rounded to 2 decimal places
- Raises `ValueError` if `items` is `None`
- Raises `ValueError` if `items` is empty
- Raises `ValueError` if any `price` is negative
- Raises `ValueError` if any `qty` is less than 1
- Raises `ValueError` if a required key (`price`, `qty`) is missing from any item

**Edge cases:**
- Single item
- Large quantity (`qty=10000`)
- Floating-point prices that accumulate rounding error (e.g. `0.1 + 0.2`)
- `qty=1` (boundary)

---

## apply_discount

```python
def apply_discount(total: float, discount_code: str) -> float
```

**Behaviors:**
- `"SAVE10"` → 10% off
- `"SAVE20"` → 20% off
- `"FREESHIP"` → no change to total (free shipping, not a price discount)
- Unknown code → raises `ValueError`
- `total <= 0` → raises `ValueError`
- Returns result rounded to 2 decimal places

---

## validate_order

```python
def validate_order(order: dict) -> bool
```

**Required fields:**
- `"items"` — non-empty list
- `"customer_email"` — must contain `"@"`

**Behaviors:**
- Returns `True` if all fields are valid
- Raises `ValueError` with a descriptive message if any field is invalid
- Raises `ValueError` if `order` is `None`
- Raises `ValueError` if `order` is missing required fields
- Raises `ValueError` if `customer_email` is empty or lacks `"@"`
- Raises `ValueError` if `items` is an empty list
