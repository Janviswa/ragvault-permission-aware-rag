from types import SimpleNamespace
from unittest.mock import patch

from app.rag.pipeline import retrieve_secure_context


def test_retrieval_uses_current_users_tenant_and_identity():
    db = object()
    current_user = SimpleNamespace(id=2, role="Employee", tenant_id="tenant_demo")

    with patch("app.rag.pipeline.search_documents", return_value=[]) as search:
        with patch("app.rag.pipeline.build_secure_context", return_value=("", [])):
            retrieve_secure_context(db, current_user, "What is RAGVault?", limit=5)

    search.assert_called_once_with(
        query="What is RAGVault?",
        tenant_id="tenant_demo",
        user_id=2,
        role="Employee",
        limit=5,
    )


def test_cross_tenant_result_is_not_added_to_secure_context():
    from app.rag.security import verify_retrieved_documents

    current_user = SimpleNamespace(id=2, role="Employee", tenant_id="tenant_demo")
    result = SimpleNamespace(payload={"document_id": 99})

    class DB:
        def get(self, model, document_id):
            return SimpleNamespace(id=document_id, tenant_id="other_tenant")

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

    assert verify_retrieved_documents(DB(), current_user, [result]) == []
