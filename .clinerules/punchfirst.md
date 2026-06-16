# punchfirst

The test throws the first punch. Always.

Before any production code:

```
1. Is there a failing test for this?          → no test = no code
2. Does the test test behavior, not internals? → rewrite the test first
3. Is this the smallest test that proves it?   → shrink it
4. Does the name describe the scenario?        → rename it
5. Only then: write the minimum code to pass
6. Refactor — only when green
```

**Test rules:** Public interfaces only. One behavior per test. Names read like specs. Cover `None`/empty/boundaries/errors. Parametrize before duplicating. Mock only external IO. Delete tests that assert on implementation details.

**SE principles:** YAGNI — no test = don't build it. SRP — complex test setup = function does too much, split it. DIP — inject all external deps. Fail fast — every input function needs `pytest.raises` tests. DRY (tests) — parametrize over duplicate. DRY (prod) — tests don't always catch it; identical test clusters are the signal. KISS — hard-to-write test = design problem.

**Never removed:** security tests, data mutation tests, error handling tests, API contract tests.
