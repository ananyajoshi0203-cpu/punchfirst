# punchfirst

The test throws the first punch. Always.

## Protocol

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
- One behavior per test
- Names: `test_login_with_expired_token_raises_auth_error`
- Cover: `None`, empty, boundary values, error paths
- `@pytest.mark.parametrize` before duplicating
- Mock only external services/IO
- Delete tests that assert on implementation details

## SE principles

- **YAGNI**: no failing test = don't build it
- **SRP**: complex test setup = function does too much, split it
- **DIP**: inject all external deps — can't inject = can't test
- **Fail fast**: every function with inputs needs `pytest.raises` tests
- **DRY (tests)**: parametrize before duplicating
- **DRY (prod)**: tests don't always catch it — identical test clusters are the signal
- **KISS**: hard-to-write test = design problem

## Never removed

- Security/auth tests
- Data mutation tests
- Error handling tests
- API contract tests
