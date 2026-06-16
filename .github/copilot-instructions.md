# punchfirst

The test throws the first punch. Always.

Before suggesting any production code, check:
1. Does a failing test exist for this behavior? If not, suggest the test first.
2. Does the test test behavior, not internals? If not, rewrite it.
3. Is this the minimum code to pass? Don't add more.
4. Refactor only after green.

Test suggestions must:
- Test public interfaces only — no private methods
- Cover one behavior per test
- Use names like: `test_login_with_expired_token_raises_auth_error`
- Include edge cases: `None`, empty, boundary values, error paths
- Use `@pytest.mark.parametrize` instead of duplicating similar tests

SE principles to apply:
- YAGNI: no failing test = don't suggest it
- SRP: if test setup is complex, suggest splitting the function first
- DIP: suggest injectable dependencies for anything external (DB, HTTP, time, filesystem)
- Fail fast: every function with inputs needs `pytest.raises` coverage
- DRY (tests): suggest parametrize when similar tests appear
- DRY (prod): flag as a refactor note — tests don't always catch duplication
- KISS: complex test setup = design smell, simplify the unit

Never suggest:
- Production code without a test
- Tests named `test_works`, `test_it`, `test_function`
- Mocking a class this codebase owns
- `@pytest.mark.skip` without a comment
