from types import SimpleNamespace
from unittest.mock import patch

from app.security.audit import create_audit_log
from app.security.acl import check_document_access


class DB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = 77

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        class Query:
            def filter(self, *args):
                return self

            def first(self):
                return None

        return Query()


def test_create_audit_log_persists_expected_fields():
    db = DB()
    log = create_audit_log(
        db,
        user_id=2,
        tenant_id="tenant_demo",
        action="document_access",
        resource_type="document",
        resource_id=3,
        details="test",
    )

    assert log.id == 77
    assert log.user_id == 2
    assert log.tenant_id == "tenant_demo"
    assert log.action == "document_access"
    assert log.resource_type == "document"
    assert log.resource_id == "3"
    assert log.status == "success"


def test_unauthorized_access_creates_security_event():
    db = DB()
    employee = SimpleNamespace(id=2, role="Employee", tenant_id="tenant_demo")
    doc = SimpleNamespace(id=3, tenant_id="tenant_demo")

    with patch("app.security.acl.create_security_event") as event:
        import pytest
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            check_document_access(db, employee, doc)

    event.assert_called_once()
    assert event.call_args.kwargs["event_type"] == "unauthorized_document_access"
    assert event.call_args.kwargs["severity"] == "high"
