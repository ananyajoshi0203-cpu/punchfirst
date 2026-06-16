# punchfirst

The test throws the first punch. Always.

## Protocol — run before every code-writing task

### Step 0 — read the spec

Tests are derived from specs. Before writing anything, extract from the provided documentation:

- **Behaviors**: what does this do in the normal case?
- **Inputs / outputs**: types, return values, what "not found" looks like
- **Error cases**: what inputs are invalid, what should be raised
- **Edge cases**: `None`, empty, zero, negative, boundary values

Accepted formats: docstrings, OpenAPI/Swagger YAML, markdown requirements, user stories, function signatures with type hints, or plain natural language.

If no spec is provided, ask before writing anything. Do not infer the spec from thin air.

Once the spec is read, list all test cases before writing a single test.

### Step 1–6 — Red → Green → Refactor

```
1. Is there a failing test for this?          → no test = no code
2. Does the test test behavior, not internals? → rewrite the test first
3. Is this the smallest test that proves it?   → shrink it
4. Does the name describe the scenario?        → rename it
5. Only then: write the minimum code to pass
6. Refactor — only when green
```

## Test rules

- Public interfaces only — never `._private_method()`
- One behavior per test — "and" in the name = split it
- Names read like specs: `test_login_with_expired_token_raises_auth_error`
- Always cover: `None`, empty collections, boundary values, error paths
- `@pytest.mark.parametrize` before duplicating a test
- Mock only external services and I/O — never your own classes
- Delete tests that assert on implementation details

## Minimalism

- `pytest` before `unittest` before custom frameworks
- `assert` before adding assertion libraries
- Standard library before a new dependency
- One fixture over five setup methods

## SE principles

**YAGNI** — no failing test = don't build it.

**SRP** — complex test setup for one function = that function does too much. Split it.

**DIP** — all external dependencies (DB, HTTP, time, filesystem) must be injectable. Can't inject it = can't test it in isolation.

**Fail fast** — validate at the boundary, raise early. Every function with inputs needs error path tests (`pytest.raises`).

**DRY (tests)** — `@pytest.mark.parametrize` before copy-pasting a test. Duplicated test logic diverges silently.

**DRY (production code)** — tests don't always catch this. Identical test clusters are the signal; fix it in the refactor step, only when green.

**KISS** — hard-to-write test = design problem. Simplify the unit, not the test.

## Never skipped

- Security and auth boundary tests
- Data mutation and deletion tests
- Error handling and exception path tests
- API contract tests

## Never done

- Production code before a failing test
- Tests named `test_works`, `test_it`, or `test_function`
- Mocking a class this codebase owns
- `pass` in a test body
- `@pytest.mark.skip` without a comment
