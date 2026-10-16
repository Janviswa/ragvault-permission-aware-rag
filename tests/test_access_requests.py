from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.documents.access_requests import AccessRequestCreate, request_access


class Query:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class DB:
    def __init__(self, document=None, existing=None):
        self.document = document
        self.existing = existing
        self.added = []
        self.refreshed = []

    def get(self, model, object_id):
        return self.document

    def query(self, model):
        return Query(self.existing)

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = 101

    def commit(self):
        pass

    def refresh(self, obj):
        self.refreshed.append(obj)


def test_access_request_is_created():
    db = DB(document=SimpleNamespace(id=3, tenant_id="tenant_demo"))
    current_user = SimpleNamespace(id=2, tenant_id="tenant_demo")

    with patch("app.documents.access_requests.create_audit_log"):
        response = request_access(
            3,
            AccessRequestCreate(reason="Need the project documentation"),
            db,
            current_user,
        )

    assert response["message"] == "Access request submitted"
    assert response["request_id"] == 101
    assert len(db.added) == 1
    assert db.added[0].status == "pending"
    assert db.added[0].user_id == 2


def test_duplicate_pending_request_is_rejected():
    existing = SimpleNamespace(id=100, status="pending")
    db = DB(document=SimpleNamespace(id=3, tenant_id="tenant_demo"), existing=existing)
    current_user = SimpleNamespace(id=2, tenant_id="tenant_demo")

    with pytest.raises(HTTPException) as exc:
        request_access(3, AccessRequestCreate(), db, current_user)

    assert exc.value.status_code == 409
