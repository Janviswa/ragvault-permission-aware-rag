import pytest
from fastapi import HTTPException

from app.rag.security import verify_retrieved_documents
from unittest.mock import patch

def test_retrieved_document_is_allowed():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 3
        tenant_id = "tenant_demo"

    class MockPermission:
        document_id = 3
        user_id = 1
        role = None
        permission = "read"

    class MockResult:
        payload = {
            "document_id": 3,
            "tenant_id": "tenant_demo",
        }

    class MockQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *args):
            return self

        def first(self):
            return self.result

    class MockDB:
        def __init__(self):
            self.query_count = 0

        def get(self, model, document_id):
            return MockDocument()

        def query(self, model):
            self.query_count += 1

            if self.query_count == 1:
                return MockQuery(None)

            return MockQuery(MockPermission())

    results = verify_retrieved_documents(
        MockDB(),
        MockUser(),
        [MockResult()],
    )

    assert len(results) == 1


def test_retrieved_document_without_document_id_is_removed():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockResult:
        payload = {
            "tenant_id": "tenant_demo",
        }

    class MockDB:
        pass

    results = verify_retrieved_documents(
        MockDB(),
        MockUser(),
        [MockResult()],
    )

    assert results == []

def test_cross_tenant_retrieved_document_is_removed():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 10
        tenant_id = "tenant_other"

    class MockResult:
        payload = {
            "document_id": 10,
            "tenant_id": "tenant_other",
            "text": "SECRET OTHER TENANT DATA",
        }

    class MockDB:
        def get(self, model, document_id):
            return MockDocument()

        def query(self, model):
            class Query:
                def filter(self, *args):
                    return self

                def first(self):
                    return None

            return Query()

        def add(self, item):
            pass

        def commit(self):
            pass

        def refresh(self, item):
            pass

    results = verify_retrieved_documents(
        MockDB(),
        MockUser(),
        [MockResult()],
    )

    assert results == []


def test_unauthorized_retrieved_document_is_removed():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 10
        tenant_id = "tenant_demo"

    class MockResult:
        payload = {
            "document_id": 10,
            "tenant_id": "tenant_demo",
            "text": "SECRET UNAUTHORIZED DATA",
        }

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class MockDB:
        def get(self, model, document_id):
            return MockDocument()

        def query(self, model):
            return MockQuery()

        def add(self, item):
            pass

        def commit(self):
            pass

        def refresh(self, item):
            pass

    results = verify_retrieved_documents(
        MockDB(),
        MockUser(),
        [MockResult()],
    )

    assert results == []

def test_expired_temporary_access_is_removed():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 20
        tenant_id = "tenant_demo"

    class MockResult:
        payload = {
            "document_id": 20,
            "tenant_id": "tenant_demo",
            "text": "SECRET TEMPORARY DATA",
        }

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class MockDB:
        def get(self, model, document_id):
            return MockDocument()

        def query(self, model):
            return MockQuery()

        def add(self, item):
            pass

        def commit(self):
            pass

        def refresh(self, item):
            pass

    results = verify_retrieved_documents(
        MockDB(),
        MockUser(),
        [MockResult()],
    )

    assert results == []

def test_revoked_permission_removes_retrieved_document():

    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockResult:
        payload = {
            "document_id": 42,
            "tenant_id": "tenant_demo",
            "title": "Revoked Document",
            "text": "This should not be visible.",
        }

    class MockDocument:
        id = 42
        tenant_id = "tenant_demo"

    class MockDB:
        def get(self, model, document_id):
            return MockDocument()

    db = MockDB()

    with patch(
        "app.rag.security.check_document_access",
        side_effect=HTTPException(status_code=403, detail="Document access denied"),
    ):
        authorized_results = verify_retrieved_documents(
            db,
            MockUser(),
            [MockResult()],
        )

    assert authorized_results == []


def test_qdrant_query_uses_tenant_and_user_role_acl_filters():
    from app.rag.retrieval import search_documents

    class Client:
        def query_points(self, **kwargs):
            self.query = kwargs
            return type("Response", (), {"points": []})()

    client = Client()
    with patch("app.rag.retrieval.generate_embedding", return_value=[0.0]), patch(
        "app.rag.retrieval.get_client",
        return_value=client,
    ):
        search_documents(
            query="safe question",
            tenant_id="tenant_demo",
            user_id=7,
            role="Employee",
        )

    query_filter = client.query["query_filter"]
    assert [(condition.key, condition.match.value) for condition in query_filter.must] == [
        ("tenant_id", "tenant_demo")
    ]
    assert {condition.key for condition in query_filter.should} == {
        "allowed_user_ids",
        "allowed_roles",
    }
    assert query_filter.should[0].match.any == [7]
    assert query_filter.should[1].match.any == ["Employee"]


def test_unauthorized_retrieval_never_reaches_llm_and_is_audited():
    from app.rag.routes import RAGQueryRequest, query_rag

    class Query:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class DB:
        def __init__(self):
            self.added = []

        def get(self, model, document_id):
            return type("Document", (), {"id": document_id, "tenant_id": "tenant_demo"})()

        def query(self, model):
            return Query()

        def add(self, item):
            self.added.append(item)

        def commit(self):
            pass

        def refresh(self, item):
            pass

    result = type(
        "Retrieved",
        (),
        {"payload": {"document_id": 42, "text": "SECRET UNAUTHORIZED CONTENT"}},
    )()
    user = type("User", (), {"id": 1, "role": "Employee", "tenant_id": "tenant_demo"})()
    db = DB()

    with patch("app.rag.pipeline.search_documents", return_value=[result]), patch(
        "app.rag.routes.generate_answer",
        return_value="No authorized information found.",
    ) as llm:
        response = query_rag(RAGQueryRequest(question="What is private?"), db, user)

    llm.assert_called_once_with(question="What is private?", context="")
    assert response.sources == []
    assert any(getattr(item, "action", None) == "rag_query" for item in db.added)


def test_authorized_rag_query_returns_sources_and_audit_record():
    from app.models.document_permission import DocumentPermission
    from app.models.temporary_access import TemporaryAccess
    from app.rag.routes import RAGQueryRequest, query_rag

    permission = type(
        "Permission",
        (),
        {"user_id": 1, "role": None, "permission": "read"},
    )()
    result = type(
        "Retrieved",
        (),
        {
            "payload": {
                "document_id": 42,
                "title": "Authorized",
                "file_name": "authorized.txt",
                "chunk_index": 0,
                "text": "Authorized document content.",
            }
        },
    )()

    class Query:
        def __init__(self, value):
            self.value = value

        def filter(self, *args):
            return self

        def first(self):
            return self.value

    class DB:
        def __init__(self):
            self.added = []

        def get(self, model, document_id):
            return type("Document", (), {"id": 42, "tenant_id": "tenant_demo"})()

        def query(self, model):
            return Query(None if model is TemporaryAccess else permission)

        def add(self, item):
            self.added.append(item)

        def commit(self):
            pass

        def refresh(self, item):
            pass

    db = DB()
    user = type("User", (), {"id": 1, "role": "Employee", "tenant_id": "tenant_demo"})()
    with patch("app.rag.pipeline.search_documents", return_value=[result]), patch(
        "app.rag.routes.generate_answer",
        return_value="Authorized answer.",
    ) as llm:
        response = query_rag(RAGQueryRequest(question="Question"), db, user)

    assert response.answer == "Authorized answer."
    assert response.sources[0].document_id == 42
    assert response.sources[0].title == "Authorized"
    assert "Authorized document content." in llm.call_args.kwargs["context"]
    assert any(getattr(item, "action", None) == "rag_query" for item in db.added)


def test_rag_query_input_has_size_validation():
    from pydantic import ValidationError

    from app.rag.routes import RAGQueryRequest

    with pytest.raises(ValidationError):
        RAGQueryRequest(question="x" * 4001)