from types import SimpleNamespace

from app.security.acl import check_document_access


class Query:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class DB:
    def __init__(self, result=None):
        self.result = result
        self.events = []

    def query(self, model):
        return Query(self.result)

    def add(self, obj):
        self.events.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def test_admin_can_access_document_without_document_permission():
    db = DB()
    admin = SimpleNamespace(id=1, role="Admin", tenant_id="tenant_demo")
    doc = SimpleNamespace(id=3, tenant_id="tenant_demo")
    assert check_document_access(db, admin, doc) is True


def test_role_permission_allows_matching_role():
    db = DB(SimpleNamespace(permission="read"))
    manager = SimpleNamespace(id=2, role="Manager", tenant_id="tenant_demo")
    doc = SimpleNamespace(id=3, tenant_id="tenant_demo")
    assert check_document_access(db, manager, doc) is True
