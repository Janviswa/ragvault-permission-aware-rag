from types import SimpleNamespace
from unittest.mock import patch

from app.rag.context import build_secure_context
from app.rag.pipeline import retrieve_secure_context


def test_secure_context_contains_only_authorized_document_text():
    current_user = SimpleNamespace(
        id=2,
        role="Employee",
        tenant_id="tenant_demo",
    )

    result = SimpleNamespace(
        payload={
            "document_id": 3,
            "title": "RAGVault Test Document",
            "text": "RAGVault protects documents using tenant isolation.",
        }
    )

    document = SimpleNamespace(
        id=3,
        tenant_id="tenant_demo",
    )

    class DB:
        def get(self, model, document_id):
            return document

    with patch("app.rag.security.check_document_access", return_value=True):
        context, authorized_results = build_secure_context(
            DB(),
            current_user,
            [result],
        )

    assert "RAGVault Test Document" in context
    assert "tenant isolation" in context
    assert len(authorized_results) == 1


def test_pipeline_passes_authenticated_identity_to_retriever():
    db = object()

    current_user = SimpleNamespace(
        id=2,
        role="Employee",
        tenant_id="tenant_demo",
    )

    with patch(
        "app.rag.pipeline.search_documents",
        return_value=[],
    ) as search:

        with patch(
            "app.rag.pipeline.build_secure_context",
            return_value=("authorized context", []),
        ):

            context, authorized_results = retrieve_secure_context(
                db,
                current_user,
                "What is RAGVault?",
                limit=5,
            )

    assert context == "authorized context"
    assert authorized_results == []

    search.assert_called_once_with(
        query="What is RAGVault?",
        tenant_id="tenant_demo",
        user_id=2,
        role="Employee",
        limit=5,
    )

def test_pipeline_excludes_cross_tenant_document():
    current_user = SimpleNamespace(
        id=2,
        role="Employee",
        tenant_id="tenant_demo",
    )

    cross_tenant_result = SimpleNamespace(
        payload={
            "document_id": 20,
            "tenant_id": "tenant_other",
            "title": "Other Tenant Secret",
            "text": "SECRET DATA FROM ANOTHER TENANT.",
        }
    )

    with patch(
        "app.rag.pipeline.search_documents",
        return_value=[cross_tenant_result],
    ):

        with patch(
            "app.rag.pipeline.build_secure_context",
            return_value=("", []),
        ):

            context, authorized_results = retrieve_secure_context(
                db=object(),
                current_user=current_user,
                query="secret data",
                limit=5,
            )

    assert "SECRET DATA FROM ANOTHER TENANT." not in context
    assert "Other Tenant Secret" not in context
    assert authorized_results == []