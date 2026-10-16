from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.security.acl import check_document_access
from app.models.document_permission import DocumentPermission
from app.models.security_event import SecurityEvent
from app.models.temporary_access import TemporaryAccess


class Query:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class DB:
    def __init__(self, temporary=None):
        self.temporary = temporary
        self.events = []

    def query(self, model):
        if model is TemporaryAccess:
            active = (
                self.temporary
                if self.temporary and self.temporary.expires_at > datetime.utcnow()
                else None
            )
            return Query(active)
        if model is DocumentPermission:
            return Query(None)
        if model is SecurityEvent:
            return Query(None)
        raise AssertionError(f"Unexpected model: {model}")

    def add(self, obj):
        self.events.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def make_user():
    return SimpleNamespace(id=2, role="Employee", tenant_id="tenant_demo")


def make_doc():
    return SimpleNamespace(id=3, tenant_id="tenant_demo")


def test_active_temporary_access_allows_document_access():
    grant = SimpleNamespace(expires_at=datetime.utcnow() + timedelta(minutes=5))
    assert check_document_access(DB(grant), make_user(), make_doc()) is True


def test_expired_temporary_access_does_not_allow_access():
    grant = SimpleNamespace(expires_at=datetime.utcnow() - timedelta(seconds=1))
    with pytest.raises(HTTPException) as exc:
        check_document_access(DB(grant), make_user(), make_doc())
    assert exc.value.status_code == 403
