from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
import asyncio

import pytest
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from jose import jwt

from app.auth.dependencies import get_current_user, require_role
from app.auth.routes import register
from app.auth.routes import router as auth_router
from app.config import settings
from app.main import validation_error_handler
from app.security.jwt import create_access_token


def test_invalid_and_expired_tokens_are_rejected():
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    for token in ("not-a-jwt", expired):
        with pytest.raises(HTTPException) as exc:
            get_current_user(
                credentials=SimpleNamespace(credentials=token),
                db=SimpleNamespace(get=lambda *_: None),
            )
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or expired token"


def test_missing_bearer_credentials_are_rejected_with_401():
    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=None,
            db=SimpleNamespace(get=lambda *_: None),
        )

    assert exc.value.status_code == 401
    assert exc.value.headers["WWW-Authenticate"] == "Bearer"


def test_inactive_user_is_rejected_even_with_a_valid_token():
    token = create_access_token(user_id=4, tenant_id="tenant_demo", role="Employee")
    db = SimpleNamespace(get=lambda *_: SimpleNamespace(is_active=False))

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=SimpleNamespace(credentials=token),
            db=db,
        )

    assert exc.value.status_code == 401


def test_role_dependency_denies_non_admin_and_accepts_admin():
    checker = require_role("Admin")

    with pytest.raises(HTTPException) as exc:
        checker(current_user=SimpleNamespace(role="Employee"))
    assert exc.value.status_code == 403
    assert checker(current_user=SimpleNamespace(role="Admin")).role == "Admin"


def test_auth_router_has_no_debug_admin_endpoint():
    assert all(route.path != "/auth/admin-test" for route in auth_router.routes)


def test_public_registration_is_disabled():
    with pytest.raises(HTTPException) as exc:
        register()

    assert exc.value.status_code == 403
    assert "tenant administrator" in exc.value.detail.lower()


def test_validation_errors_do_not_echo_sensitive_input():
    request = Request({"type": "http", "method": "POST", "path": "/auth/login", "headers": []})
    exc = RequestValidationError(
        [
            {
                "loc": ("body", "password"),
                "msg": "Invalid value",
                "type": "value_error",
                "input": "sensitive-password",
            }
        ]
    )

    response = asyncio.run(validation_error_handler(request, exc))

    assert response.status_code == 422
    assert b"sensitive-password" not in response.body
