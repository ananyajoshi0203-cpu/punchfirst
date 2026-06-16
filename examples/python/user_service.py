# examples/python/user_service.py
#
# This file is written AFTER test_user_service.py.
# The spec defined the contract. The tests verified it. Now the code fulfills it.
#
# Step 2 — minimum code to make all tests pass (GREEN).

from __future__ import annotations


def get_user(user_id: int) -> "User | None":
    """
    Returns the user with the given ID.
    Returns None if no user exists with that ID.
    Raises ValueError if user_id is None or not a positive integer.
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"user_id must be a positive integer, got {user_id!r}")
    return db.query(User).filter_by(id=user_id).first()


# Step 3 — refactor (only now, only while green).
# Nothing to refactor — it's already the minimum that satisfies the spec.
