---
title: punchfirst — strict TDD enforcer
inclusion: always
---

# punchfirst

The test throws the first punch. Always.

Before writing any production code, run the protocol:

```
1. Is there a failing test for this?          → no test = no code
2. Does the test test behavior, not internals? → rewrite the test first
3. Is this the smallest test that proves it?   → shrink it
4. Does the name describe the scenario?        → rename it
5. Only then: write the minimum code to pass
6. Refactor — only when green
```

Before any failing test, read the spec. Extract behaviors, inputs, outputs, error cases, and edge cases. If no spec is provided, ask — do not infer from thin air.

## Test rules

- Public interfaces only — never `._private_method()`
- One behavior per test — "and" in the name = split it
- Names read like specs: `test_login_with_expired_token_raises_auth_error`
- Always cover: `None`, empty collections, boundary values, error paths
- `@pytest.mark.parametrize` before duplicating a test
- Mock only external services and I/O — never your own classes
- Delete tests that assert on implementation details

## SE principles

- **YAGNI**: no failing test = don't build it
- **SRP**: complex test setup for one function = split the function
- **DIP**: inject all external deps (DB, HTTP, time, filesystem) — can't inject = can't test
- **Fail fast**: every function with inputs needs `pytest.raises` tests
- **DRY (tests)**: parametrize before duplicating
- **DRY (prod)**: identical test clusters are the signal — fix in refactor step only
- **KISS**: hard-to-write test = design problem, not test problem

## Never

- Production code before a failing test
- Tests named `test_works`, `test_it`
- Mocking a class you own
- `pass` in a test body
- `@pytest.mark.skip` without a comment

## Never removed

- Security and auth boundary tests
- Data mutation and deletion tests
- Error handling and exception path tests
- API contract tests
