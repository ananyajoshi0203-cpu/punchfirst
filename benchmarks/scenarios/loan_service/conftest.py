# conftest.py
#
# Shared fixtures for both suites.
# Each fixture returns a dict of loan parameters; tests unpack with **loan.

import pytest


@pytest.fixture
def personal_loan():
    """Short-tenure unsecured loan. Common in consumer fintech."""
    return {"principal": 200_000, "annual_rate_percent": 14.0, "tenure_months": 24}


@pytest.fixture
def home_loan():
    """Long-tenure mortgage. Rounding drift is pronounced over 240 months."""
    return {"principal": 5_000_000, "annual_rate_percent": 8.5, "tenure_months": 240}


@pytest.fixture
def bridge_loan():
    """Very short tenure at a high rate. Tests boundary at 1-month EMI calculation."""
    return {"principal": 500_000, "annual_rate_percent": 18.0, "tenure_months": 3}


@pytest.fixture
def microfinance_loan():
    """Small principal, high rate. Common in NBFC lending."""
    return {"principal": 25_000, "annual_rate_percent": 24.0, "tenure_months": 12}


@pytest.fixture
def loan_factory():
    """Returns a function that builds arbitrary loan parameter dicts."""

    def _make(principal=100_000, annual_rate_percent=12.0, tenure_months=12):
        return {
            "principal": principal,
            "annual_rate_percent": annual_rate_percent,
            "tenure_months": tenure_months,
        }

    return _make
