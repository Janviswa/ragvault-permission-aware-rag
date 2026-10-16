from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.admin.access_requests import approve_access_request, reject_access_request
from app.admin.users import list_users
from app.documents.permissions import revoke_permission
from app.documents.routes import (
    TemporaryAccessRequest,
    grant_temporary_access,
    revoke_temporary_access,
)
from app.models.access_request import AccessRequest
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.temporary_access import TemporaryAccess
from app.models.user import User


def test_cross_tenant_document_permission_idor_does_not_revoke():
    document = SimpleNamespace(id=9, tenant_id="tenant_b")
    permission = SimpleNamespace(id=20, document_id=9)

    class DB:
        def get(self, model, object_id):
            return document if model is Document else permission

        def delete(self, item):
            raise AssertionError("Permission must remain unchanged")

        def commit(self):
            raise AssertionError("Cross-tenant operation must not commit")

    with pytest.raises(HTTPException) as exc:
        revoke_permission(
            9,
            20,
            DB(),
            SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin"),
        )

    assert exc.value.status_code == 403


def test_cross_tenant_temporary_access_idor_does_not_revoke():
    document = SimpleNamespace(id=9, tenant_id="tenant_b")
    access = SimpleNamespace(id=30, document_id=9, user_id=4)

    class DB:
        def get(self, model, object_id):
            return document if model is Document else access

        def delete(self, item):
            raise AssertionError("Temporary grant must remain unchanged")

        def commit(self):
            raise AssertionError("Cross-tenant operation must not commit")

    with pytest.raises(HTTPException) as exc:
        revoke_temporary_access(
            9,
            30,
            DB(),
            SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin"),
        )

    assert exc.value.status_code == 403


def test_cross_tenant_access_request_idor_does_not_approve():
    request = SimpleNamespace(id=40, status="pending", document_id=9, user_id=4)
    document = SimpleNamespace(id=9, tenant_id="tenant_b")
    target = SimpleNamespace(id=4, tenant_id="tenant_b")

    class DB:
        def __init__(self):
            self.added = []

        def get(self, model, object_id):
            if model is AccessRequest:
                return request
            if model is Document:
                return document
            if model is User:
                return target
            raise AssertionError(f"Unexpected model: {model}")

        def add(self, item):
            self.added.append(item)

        def commit(self):
            raise AssertionError("Cross-tenant operation must not commit")

    db = DB()
    with pytest.raises(HTTPException) as exc:
        approve_access_request(
            40,
            SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin"),
            db,
        )

    assert exc.value.status_code == 403
    assert request.status == "pending"
    assert db.added == []


def test_temporary_access_grant_accepts_timezone_aware_expiry_and_syncs_acl():
    document = SimpleNamespace(id=9, tenant_id="tenant_a")
    target = SimpleNamespace(id=4, tenant_id="tenant_a")

    class DB:
        def __init__(self):
            self.added = []

        def get(self, model, object_id):
            return document if model is Document else target

        def add(self, item):
            item.id = 31
            self.added.append(item)

        def commit(self):
            pass

        def refresh(self, item):
            pass

    db = DB()
    admin = SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin")
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    with patch("app.documents.routes.sync_document_permissions") as sync, patch(
        "app.documents.routes.create_audit_log"
    ):
        response = grant_temporary_access(
            9,
            TemporaryAccessRequest(user_id=4, expires_at=expiry),
            db,
            admin,
        )

    sync.assert_called_once_with(db=db, document_id=9)
    assert response["access_id"] == 31
    assert db.added[0].expires_at.tzinfo is None


def test_permission_revoke_syncs_qdrant_after_database_revoke():
    document = SimpleNamespace(id=9, tenant_id="tenant_a")
    permission = SimpleNamespace(id=20, document_id=9)

    class DB:
        def __init__(self):
            self.deleted = None

        def get(self, model, object_id):
            return document if model is Document else permission

        def delete(self, item):
            self.deleted = item

        def commit(self):
            pass

    db = DB()
    with patch("app.documents.permissions.sync_document_permissions") as sync, patch(
        "app.documents.permissions.create_audit_log"
    ):
        result = revoke_permission(
            9,
            20,
            db,
            SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin"),
        )

    assert db.deleted is permission
    sync.assert_called_once_with(db=db, document_id=9)
    assert result["permission_id"] == 20


def test_access_request_approval_grants_permission_and_syncs_qdrant():
    access_request = SimpleNamespace(
        id=40,
        status="pending",
        document_id=9,
        user_id=4,
        decided_at=None,
    )
    document = SimpleNamespace(id=9, tenant_id="tenant_a")
    target = SimpleNamespace(id=4, tenant_id="tenant_a")

    class DB:
        def __init__(self):
            self.added = []

        def get(self, model, object_id):
            if model is AccessRequest:
                return access_request
            if model is Document:
                return document
            if model is User:
                return target
            raise AssertionError(f"Unexpected model: {model}")

        def add(self, item):
            self.added.append(item)

        def commit(self):
            pass

        def refresh(self, item):
            pass

    db = DB()
    with patch("app.admin.access_requests.sync_document_permissions") as sync:
        result = approve_access_request(
            40,
            SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin"),
            db,
        )

    permission = next(item for item in db.added if isinstance(item, DocumentPermission))
    sync.assert_called_once_with(db=db, document_id=9)
    assert permission.user_id == 4
    assert permission.permission == "read"
    assert result["status"] == "approved"


def test_temporary_access_revoke_removes_record_and_syncs_acl():
    document = SimpleNamespace(id=9, tenant_id="tenant_a")
    access = SimpleNamespace(id=30, document_id=9, user_id=4)
    target = SimpleNamespace(id=4)

    class DB:
        def __init__(self):
            self.deleted = None

        def get(self, model, object_id):
            if model is Document:
                return document
            if model is TemporaryAccess:
                return access
            if model is User:
                return target
            raise AssertionError(f"Unexpected model: {model}")

        def delete(self, item):
            self.deleted = item

        def commit(self):
            pass

    db = DB()
    with patch("app.documents.routes.sync_document_permissions") as sync, patch(
        "app.documents.routes.create_audit_log"
    ):
        result = revoke_temporary_access(
            9,
            30,
            db,
            SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin"),
        )

    assert db.deleted is access
    sync.assert_called_once_with(db=db, document_id=9)
    assert result["access_id"] == 30


def test_cross_tenant_access_request_idor_does_not_reject():
    request = SimpleNamespace(id=40, status="pending", document_id=9, user_id=4)
    document = SimpleNamespace(id=9, tenant_id="tenant_b")
    target = SimpleNamespace(id=4, tenant_id="tenant_b")

    class DB:
        def get(self, model, object_id):
            if model is AccessRequest:
                return request
            if model is Document:
                return document
            if model is User:
                return target
            raise AssertionError(f"Unexpected model: {model}")

        def commit(self):
            raise AssertionError("Cross-tenant operation must not commit")

    with pytest.raises(HTTPException) as exc:
        reject_access_request(
            40,
            SimpleNamespace(id=1, tenant_id="tenant_a", role="Admin"),
            DB(),
        )

    assert exc.value.status_code == 403
    assert request.status == "pending"


def test_admin_user_list_never_returns_password_hashes():
    user = SimpleNamespace(
        id=4,
        email="employee@example.com",
        full_name="Example User",
        role="Employee",
        is_active=True,
        password_hash="must-not-be-returned",
    )

    class Query:
        def filter(self, *args):
            return self

        def order_by(self, *args):
            return self

        def all(self):
            return [user]

    class DB:
        def query(self, model):
            return Query()

    response = list_users(DB(), SimpleNamespace(role="Admin", tenant_id="tenant_a"))

    assert response == [
        {
            "id": 4,
            "email": "employee@example.com",
            "full_name": "Example User",
            "role": "Employee",
            "is_active": True,
        }
    ]
    assert "password_hash" not in response[0]
