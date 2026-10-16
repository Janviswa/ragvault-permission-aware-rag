import pytest
from pydantic import ValidationError

from app.admin.users import create_user
from app.schemas.admin_user import AdminUserCreate
from unittest.mock import patch


class Query:
    def filter(self, *args):
        return self

    def first(self):
        return None


class DB:
    def __init__(self):
        self.added = []

    def query(self, model):
        return Query()

    def add(self, user):
        user.id = 22
        user.is_active = True
        self.added.append(user)

    def commit(self):
        pass

    def refresh(self, user):
        pass


def test_admin_creates_account_inside_own_tenant_without_returning_password():
    db = DB()
    current_admin = type(
        "Admin",
        (),
        {"id": 2, "role": "Admin", "tenant_id": "tenant_a"},
    )()
    request = AdminUserCreate(
        email="manager@example.com",
        full_name="Tenant Manager",
        password="initial-password-123",
        role="Manager",
    )

    with patch("app.admin.users.hash_password", return_value="stored-hash"), patch(
        "app.admin.users.create_audit_log"
    ) as audit:
        response = create_user(request, db, current_admin)

    user = db.added[0]
    assert user.tenant_id == "tenant_a"
    assert user.role == "Manager"
    assert user.password_hash == "stored-hash"
    assert response == {
        "id": 22,
        "email": "manager@example.com",
        "full_name": "Tenant Manager",
        "role": "Manager",
        "is_active": True,
    }
    assert "password" not in response
    assert "password_hash" not in response
    audit.assert_called_once()


def test_admin_user_creation_does_not_accept_client_tenant_id():
    with pytest.raises(ValidationError):
        AdminUserCreate(
            email="manager@example.com",
            full_name="Tenant Manager",
            password="initial-password-123",
            tenant_id="tenant_b",
        )
