import pytest
from fastapi import HTTPException

from app.security.tenant import verify_tenant_access
from app.security.acl import check_document_access


def test_cross_tenant_access_denied():
    class MockUser:
        tenant_id = "tenant_demo"

    with pytest.raises(HTTPException) as exc:
        verify_tenant_access(MockUser(), "tenant_other")

    assert exc.value.status_code == 403
    assert exc.value.detail == "Cross-tenant access denied"


def test_document_access_denied_without_permission():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 1
        tenant_id = "tenant_demo"

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class MockDB:
        def query(self, model):
            return MockQuery()

        def add(self, obj):
            pass

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    with pytest.raises(HTTPException) as exc:
        check_document_access(
            MockDB(),
            MockUser(),
            MockDocument(),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Document access denied"


def test_document_access_allowed_with_role_permission():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Manager"

    class MockDocument:
        id = 1
        tenant_id = "tenant_demo"

    class MockPermission:
        document_id = 1
        user_id = None
        role = "Manager"
        permission = "read"

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

        def query(self, model):
            self.query_count += 1

            if self.query_count == 1:
                return MockQuery(None)

            return MockQuery(MockPermission())

    result = check_document_access(
        MockDB(),
        MockUser(),
        MockDocument(),
    )

    assert result is True


def test_admin_has_document_access():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Admin"

    class MockDocument:
        id = 1
        tenant_id = "tenant_demo"

    class MockDB:
        pass

    result = check_document_access(
        MockDB(),
        MockUser(),
        MockDocument(),
    )

    assert result is True


def test_document_access_allowed_with_temporary_access():
    from datetime import datetime, timedelta

    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 1
        tenant_id = "tenant_demo"

    class MockTemporaryAccess:
        expires_at = datetime.utcnow() + timedelta(hours=1)

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return MockTemporaryAccess()

    class MockDB:
        def query(self, model):
            return MockQuery()

    result = check_document_access(
        MockDB(),
        MockUser(),
        MockDocument(),
    )

    assert result is True


def test_document_access_denied_with_expired_temporary_access():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 1
        tenant_id = "tenant_demo"

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class MockDB:
        def query(self, model):
            return MockQuery()

        def add(self, obj):
            pass

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    with pytest.raises(HTTPException) as exc:
        check_document_access(
            MockDB(),
            MockUser(),
            MockDocument(),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Document access denied"


def test_document_access_denied_after_permission_revocation():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 1
        tenant_id = "tenant_demo"

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class MockDB:
        def query(self, model):
            return MockQuery()

        def add(self, obj):
            pass

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    with pytest.raises(HTTPException) as exc:
        check_document_access(
            MockDB(),
            MockUser(),
            MockDocument(),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Document access denied"

def test_security_event_created_on_unauthorized_access():
    class MockUser:
        id = 1
        tenant_id = "tenant_demo"
        role = "Employee"

    class MockDocument:
        id = 99
        tenant_id = "tenant_demo"

    class MockQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class MockDB:
        def __init__(self):
            self.events = []

        def query(self, model):
            return MockQuery()

        def add(self, obj):
            self.events.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    db = MockDB()

    with pytest.raises(HTTPException) as exc:
        check_document_access(
            db,
            MockUser(),
            MockDocument(),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Document access denied"

    assert len(db.events) == 1

    event = db.events[0]

    assert event.event_type == "unauthorized_document_access"
    assert event.severity == "high"
    assert event.user_id == 1
    assert event.tenant_id == "tenant_demo"