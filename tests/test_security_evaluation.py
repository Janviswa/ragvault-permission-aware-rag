from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.rag.security import verify_retrieved_documents
from app.security.acl import check_document_access


class EmptyQuery:
    def filter(self, *args):
        return self

    def first(self):
        return None


class SecurityDB:
    def __init__(self, document):
        self.document = document
        self.events = []

    def get(self, model, document_id):
        return self.document

    def query(self, model):
        return EmptyQuery()

    def add(self, item):
        self.events.append(item)

    def commit(self):
        pass

    def refresh(self, item):
        pass


def test_cross_tenant_access_is_denied_and_recorded():
    user = SimpleNamespace(id=1, role="Employee", tenant_id="tenant_a")
    document = SimpleNamespace(id=2, tenant_id="tenant_b")
    db = SecurityDB(document)

    with pytest.raises(HTTPException) as exc:
        check_document_access(db, user, document)

    assert exc.value.status_code == 403
    assert db.events[0].event_type == "cross_tenant_document_access"


def test_unauthorized_retrieved_document_is_removed_before_context():
    user = SimpleNamespace(id=1, role="Employee", tenant_id="tenant_a")
    document = SimpleNamespace(id=2, tenant_id="tenant_a")
    result = SimpleNamespace(
        payload={
            "document_id": 2,
            "tenant_id": "tenant_a",
            "text": "CONFIDENTIAL CONTENT",
        }
    )

    results = verify_retrieved_documents(SecurityDB(document), user, [result])

    assert results == []
