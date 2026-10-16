from unittest.mock import patch

from app.rag.ingestion import sync_document_permissions


def test_sync_document_permissions_updates_qdrant_acl():

    class MockPermission:
        def __init__(self, user_id=None, role=None):
            self.user_id = user_id
            self.role = role
            self.permission = "read"

    class MockQuery:
        def filter(self, *args):
            return self

        def all(self):
            return [
                MockPermission(user_id=1),
                MockPermission(role="Manager"),
            ]

    class MockDB:
        def query(self, model):
            return MockQuery()

    class MockQdrantClient:
        def set_payload(self, **kwargs):
            self.payload_call = kwargs

    mock_client = MockQdrantClient()

    with patch(
        "app.rag.ingestion.get_client",
        return_value=mock_client,
    ), patch(
        "app.rag.ingestion.ensure_collection",
    ):

        sync_document_permissions(
            db=MockDB(),
            document_id=42,
        )

    assert mock_client.payload_call["collection_name"] == "ragvault_documents"

    assert mock_client.payload_call["payload"] == {
        "allowed_user_ids": [1],
        "allowed_roles": ["Manager"],
    }

    qdrant_filter = mock_client.payload_call["points"]

    assert qdrant_filter.must[0].key == "document_id"
    assert qdrant_filter.must[0].match.value == 42

def test_sync_document_permissions_clears_qdrant_acl_after_revocation():

    class MockQuery:
        def filter(self, *args):
            return self

        def all(self):
            # Permission was revoked, so nothing remains
            return []

    class MockDB:
        def query(self, model):
            return MockQuery()

    class MockQdrantClient:
        def set_payload(self, **kwargs):
            self.payload_call = kwargs

    mock_client = MockQdrantClient()

    with patch(
        "app.rag.ingestion.get_client",
        return_value=mock_client,
    ), patch(
        "app.rag.ingestion.ensure_collection",
    ):

        sync_document_permissions(
            db=MockDB(),
            document_id=42,
        )

    assert mock_client.payload_call["payload"] == {
        "allowed_user_ids": [],
        "allowed_roles": [],
    }

    qdrant_filter = mock_client.payload_call["points"]

    assert qdrant_filter.must[0].key == "document_id"
    assert qdrant_filter.must[0].match.value == 42

def test_sync_document_permissions_includes_active_temporary_access():

    class MockPermission:
        def __init__(self, user_id=None, role=None):
            self.user_id = user_id
            self.role = role
            self.permission = "read"

    class MockTemporaryAccess:
        def __init__(self, user_id):
            self.user_id = user_id

    class MockQuery:
        def __init__(self, model):
            self.model = model

        def filter(self, *args):
            return self

        def all(self):
            from app.models.temporary_access import TemporaryAccess

            if self.model is TemporaryAccess:
                return [MockTemporaryAccess(user_id=2)]

            return [MockPermission(user_id=1)]

    class MockDB:
        def query(self, model):
            return MockQuery(model)

    class MockQdrantClient:
        def set_payload(self, **kwargs):
            self.payload_call = kwargs

    mock_client = MockQdrantClient()

    with patch(
        "app.rag.ingestion.get_client",
        return_value=mock_client,
    ), patch(
        "app.rag.ingestion.ensure_collection",
    ):

        sync_document_permissions(
            db=MockDB(),
            document_id=42,
        )

    assert mock_client.payload_call["payload"] == {
        "allowed_user_ids": [1, 2],
        "allowed_roles": [],
    }