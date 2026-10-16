from app.rag.context import build_secure_context


def test_secure_context_contains_authorized_content():

    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockResult:
        payload = {
            "document_id": 3,
            "tenant_id": "tenant_demo",
            "title": "RAGVault Test Document",
            "text": "This is authorized enterprise content.",
        }

    class MockPermission:
        document_id = 3
        user_id = 1
        role = None
        permission = "read"

    class MockQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *args):
            return self

        def first(self):
            return self.result

    class MockDocument:
        id = 3
        tenant_id = "tenant_demo"

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

    context, authorized_results = build_secure_context(
        MockDB(),
        MockUser(),
        [MockResult()],
    )

    assert "authorized enterprise content" in context
    assert "RAGVault Test Document" in context
    assert len(authorized_results) == 1


def test_secure_context_empty_when_no_authorized_documents():

    class MockUser:
        id = 999
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockResult:
        payload = {
            "document_id": 3,
            "tenant_id": "tenant_demo",
            "title": "Restricted Document",
            "text": "Secret information.",
        }

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class MockDocument:
        id = 3
        tenant_id = "tenant_demo"

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

    context, authorized_results = build_secure_context(
        MockDB(),
        MockUser(),
        [MockResult()],
    )

    assert context == ""
    assert authorized_results == []