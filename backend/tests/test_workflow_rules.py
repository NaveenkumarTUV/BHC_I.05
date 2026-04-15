import pytest
from fastapi import HTTPException

from backend.app.services.bhc_workflow_service import validate_status_payment_combination


@pytest.mark.parametrize(
    "status,payment",
    [
        ("Quoted", "Pending"),
        ("Converted", "Pending"),
        ("Converted", "Paid"),
        ("Dropped", "Pending"),
    ],
)
def test_allowed_status_payment_combinations(status, payment):
    validate_status_payment_combination(status, payment)


@pytest.mark.parametrize(
    "status,payment",
    [
        ("Quoted", "Paid"),
        ("Dropped", "Paid"),
    ],
)
def test_invalid_status_payment_combinations_raise_http_400(status, payment):
    with pytest.raises(HTTPException) as exc:
        validate_status_payment_combination(status, payment)

    assert exc.value.status_code == 400


def test_unknown_status_is_not_blocked():
    # Unknown statuses are passed through; route-level enum restrictions can be added later.
    validate_status_payment_combination("On Hold", "Paid")
