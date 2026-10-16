import pytest
from fastapi import HTTPException

from app.security.classification import validate_classification


def test_valid_classification():
    validate_classification("Restricted")


def test_invalid_classification():
    with pytest.raises(HTTPException) as exc:
        validate_classification("Secret")

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid document classification"