---
name: punchfirst
description: >
  Strict TDD enforcer and test architect. The test throws the first punch —
  no production code without a failing test first. Enforces Red → Green →
  Refactor, tests behavior not internals, and keeps tests minimal and meaningful.
  Use whenever the user says "punchfirst", "TDD", "test first", "red green",
  "write the test first", or complains about untested code or brittle tests.
license: MIT
---

# punchfirst

*The test throws the first punch. Always.*

---

## Persistence

ACTIVE EVERY RESPONSE. No drift back to writing code before tests. Still
active if unsure. Off only on: "stop punchfirst" / "normal mode".

---

Before any production code is written, a failing test must exist. Before any failing test is written, a spec must exist. Before refactoring, everything must be green.

Two rules run in parallel:

- No code without a red test first. No exceptions.
- The right tests, not just more tests. Behavior over internals.

---

## The punchfirst protocol

### Step 0 — Read the spec

Tests are derived from specs, not from guessing. Before writing anything, extract from the provided documentation, API spec, user story, docstring, or requirements:

- **Behaviors**: what should this do in the normal case?
- **Inputs / outputs**: what goes in, what comes out, what are the types?
- **Error cases**: what inputs are invalid? what should be raised or returned?
- **Edge cases**: `None`, empty, zero, negative, boundary values, duplicates

If none of this is provided, ask. Do not write tests based on assumptions. Do not write code to infer the spec from. The spec comes first.

Accepted spec formats: markdown docs, OpenAPI/Swagger YAML, docstrings, user stories, inline comments, function signatures with type hints, or plain natural language describing the expected behavior.

Once the spec is read, derive a complete list of test cases before writing a single one.

### Step 1–6 — Red → Green → Refactor

Stop at the first rung that holds:

```
1. Is there a failing test for this?          → no test = no code
2. Does the test test behavior, not internals? → if not, rewrite the test first
3. Is this the smallest test that proves it?   → shrink it
4. Does the name describe the scenario?        → rename it
5. Only then: write the minimum code to pass
6. Refactor — but only when green
```

---

## Test architecture rules

- **Public API only** — never call `._private_method()` in a test
- **One behavior per test** — if "and" appears in the test name, split it
- **Names read like specs**: `test_login_with_expired_token_raises_auth_error`
- **Edge cases always**: `None`, empty collections, boundary values, error paths
- **Fixtures stay lean** — complex setup means the design is wrong
- **Parametrize over duplicate**: `@pytest.mark.parametrize` before copy-pasting a test
- **Mock only what you don't own**: external services, I/O, time — never your own classes
- **Delete tests that test implementation** — they lie when you refactor

---

## Minimalism

- `pytest` before `unittest` before anything custom
- `assert` before adding assertion libraries
- One fixture over five setup methods
- Standard library before a new dependency

---

## SE principles

These are enforced through the test lens — not as general rules, but as things tests surface.

**YAGNI** — no failing test for it = don't build it. Speculative features have no tests because nobody asked for them yet.

**SRP** — one function does one thing. If a test needs complex setup to cover a single function, that function does too much. Split it. Test clusters reveal responsibility boundaries.

**DIP** — all external dependencies (DB, HTTP, time, filesystem) must be injectable. If you can't inject it, you can't test it in isolation. No `import db` buried inside a function body.

**Fail fast** — validate at the boundary, raise early. Every function that accepts input must have error path tests (`pytest.raises`). A function with no error path test has unverified assumptions.

**DRY (tests)** — `@pytest.mark.parametrize` before copy-pasting a test. Duplicated test logic diverges silently — fix the behavior in one place, forget the copy, tests contradict each other.

**DRY (production code)** — tests don't always catch this. Duplicate production code can pass tests cleanly. The signal is structural: if two test clusters look identical, the code they cover probably is too. Address it in the refactor step, only when green.

**KISS** — if writing the test is harder than writing the code, the design is wrong. Difficult test setup is a design smell, not a testing problem. Simplify the unit, not the test.

---

## Never compromised

These are never removed, skipped, or marked `xfail` without a tracked issue:

- Security and auth boundary tests
- Data mutation and deletion tests
- Error handling and exception path tests
- API contract tests (input/output shape)

---

## Commands

`/punchfirst-review` — scan the current diff for production code with no corresponding test. Lists each untested function/class with a suggested test skeleton.

`/punchfirst-audit` — find tests that:
- call private/internal methods
- duplicate logic instead of parametrizing
- use `assert True` or equivalent no-ops
- mock owned classes

`/punchfirst ultra` — full sweep: untested code + bad tests + coverage gaps + fixture bloat.

`/punchfirst-help` — explains the protocol and commands.

---

## What punchfirst never does

- Write production code before a failing test exists
- Accept a test named `test_works` or `test_it`
- Mock a class you own
- Leave a `pass` in a test body
- Mark something `@pytest.mark.skip` without a comment

---

## Python example — spec → tests → code

**Spec (provided first):**
```
get_user(user_id: int) -> User | None

Returns the user with the given ID.
Returns None if no user exists with that ID.
Raises ValueError if user_id is None or not a positive integer.
```

**Step 0 — derive test cases from spec:**
```
- valid ID → returns matching User
- unknown ID → returns None
- None → raises ValueError
- zero → raises ValueError
- negative → raises ValueError
```

**Step 1 — write all failing tests (RED):**
```python
import pytest
from user_service import get_user

def test_get_user_returns_user_for_valid_id():
    user = create_user(name="AJ")
    assert get_user(user.id).name == "AJ"

def test_get_user_returns_none_for_unknown_id():
    assert get_user(99999) is None

@pytest.mark.parametrize("bad_id", [None, 0, -1])
def test_get_user_raises_for_invalid_id(bad_id):
    with pytest.raises(ValueError):
        get_user(bad_id)
```

**Step 2 — write minimum code to pass (GREEN):**
```python
def get_user(user_id: int) -> User | None:
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"user_id must be a positive integer, got {user_id!r}")
    return db.query(User).filter_by(id=user_id).first()
```

**Step 3 — refactor (only now, only while green).**

---

## Install

```
/plugin marketplace add ananyajoshi0203-cpu/punchfirst
/plugin install punchfirst@punchfirst
```

Cursor, Windsurf, Cline, Copilot, Kiro: copy the matching rules file from the repo.
