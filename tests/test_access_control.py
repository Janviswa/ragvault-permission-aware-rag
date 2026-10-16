from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.security.acl import check_document_access


class FakeQuery:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, temporary=None, user_permission=None, role_permission=None):
        self.temporary = temporary
        self.user_permission = user_permission
        self.role_permission = role_permission
        self.events = []

    def query(self, model):
        name = getattr(model, "__name__", "")
        if name == "TemporaryAccess":
            return FakeQuery(self.temporary)
        if name == "DocumentPermission":
            # ACL checks user permission first, then role permission.
            return FakeQuery(self.user_permission or self.role_permission)
        return FakeQuery(None)

    def add(self, obj):
        self.events.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def user(user_id=2, role="Employee", tenant="tenant_demo"):
    return SimpleNamespace(id=user_id, role=role, tenant_id=tenant)


def document(document_id=3, tenant="tenant_demo"):
    return SimpleNamespace(id=document_id, tenant_id=tenant)


def test_user_permission_allows_access():
    db = FakeDB(user_permission=SimpleNamespace(permission="read"))
    assert check_document_access(db, user(), document()) is True


def test_missing_permission_denies_access():
    db = FakeDB()
    with pytest.raises(HTTPException) as exc:
        check_document_access(db, user(), document())
    assert exc.value.status_code == 403
    assert exc.value.detail == "Document access denied"


def test_cross_tenant_access_is_denied():
    db = FakeDB()
    with pytest.raises(HTTPException) as exc:
        check_document_access(db, user(tenant="tenant_a"), document(tenant="tenant_b"))
    assert exc.value.status_code == 403
    assert exc.value.detail == "Cross-tenant access denied"


def test_temporary_access_allows_access_when_not_expired():
    temporary = SimpleNamespace(expires_at=datetime.utcnow() + timedelta(minutes=10))
    db = FakeDB(temporary=temporary)
    assert check_document_access(db, user(), document()) is True
