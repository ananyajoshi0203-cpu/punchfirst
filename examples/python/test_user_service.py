# examples/python/test_user_service.py
#
# Spec (provided before any code was written):
#
#   get_user(user_id: int) -> User | None
#
#   Returns the user with the given ID.
#   Returns None if no user exists with that ID.
#   Raises ValueError if user_id is None or not a positive integer.
#
# Step 0 — test cases derived from spec:
#   - valid ID          → returns matching User
#   - unknown ID        → returns None
#   - None              → raises ValueError
#   - zero              → raises ValueError
#   - negative          → raises ValueError
#
# Step 1 — all tests written first (RED), before user_service.py exists.

import pytest
from user_service import get_user


def test_get_user_returns_user_for_valid_id():
    user = create_user(name="AJ")
    result = get_user(user.id)
    assert result.name == "AJ"


def test_get_user_returns_none_for_unknown_id():
    assert get_user(99999) is None


@pytest.mark.parametrize("bad_id", [None, 0, -1])
def test_get_user_raises_for_invalid_id(bad_id):
    with pytest.raises(ValueError):
        get_user(bad_id)


# What punchfirst would reject:
#
# BAD — test derived from reading existing code, not the spec:
# def test_get_user_calls_filter_by():
#     with patch("user_service.db") as mock_db:
#         get_user(1)
#         mock_db.query().filter_by.assert_called_with(id=1)  # testing internals
#
# BAD — no spec, pure assumption:
# def test_get_user_works():
#     assert get_user(1) is not None  # "not None" is not a spec
#
# BAD — name describes implementation, not behavior:
# def test_get_user_queries_database():
#     ...
