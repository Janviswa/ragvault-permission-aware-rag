"""Test harness for the endpoints the web UI depends on.

Runs the real FastAPI app against SQLite and an in-memory Qdrant. Only the two
things that need network downloads are replaced:

* the sentence-transformers model -> a deterministic hashed bag-of-words embedder
* the LLM call -> a stub that echoes the authorized context

Run on its own:  pytest -q tests/ui_api
"""
import hashlib
import os
import re
import sys
import time
import types

os.environ["DATABASE_URL"] = "sqlite:///./ui_api_test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["GROQ_API_KEY"] = "unused"
# Hashed bag-of-words cosine scores run lower than MiniLM's, so use a lower floor here.
os.environ["RESTRICTED_MATCH_MIN_SCORE"] = "0.15"

import numpy as np  # noqa: E402


class FakeSentenceTransformer:
    DIM = 384

    def __init__(self, *args, **kwargs):
        pass

    def _one(self, text: str):
        vector = np.zeros(self.DIM, dtype=np.float32)
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            index = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.DIM
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def encode(self, texts, normalize_embeddings=True):
        if isinstance(texts, str):
            return self._one(texts)
        return np.stack([self._one(t) for t in texts])


fake_module = types.ModuleType("sentence_transformers")
fake_module.SentenceTransformer = FakeSentenceTransformer
sys.modules["sentence_transformers"] = fake_module

import qdrant_client  # noqa: E402

_memory_client = qdrant_client.QdrantClient(":memory:")
qdrant_client.QdrantClient = lambda *a, **k: _memory_client

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.rag.llm as llm  # noqa: E402

LLM_CALLS: list[str] = []


STREAM_DELAY = float(os.environ.get("FAKE_STREAM_DELAY", "0"))


def _fake_text(context: str) -> str:
    if not context:
        return "I could not find any information you are authorized to access."
    return "From the documents: " + " ".join(context.split())[:160]


def fake_generate_answer(question: str, context: str) -> str:
    LLM_CALLS.append(question)
    return _fake_text(context)


def fake_stream_answer(question: str, context: str):
    """Yields the answer word by word. 'boom-early' / 'boom-late' in the question inject failures."""
    LLM_CALLS.append(question)
    if "boom-early" in question:
        raise RuntimeError("provider down")
    for index, word in enumerate(_fake_text(context).split(" ")):
        if "boom-late" in question and index == 3:
            raise RuntimeError("connection dropped")
        if STREAM_DELAY:
            time.sleep(STREAM_DELAY)
        yield word if index == 0 else " " + word


llm.generate_answer = fake_generate_answer
llm.stream_answer = fake_stream_answer

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.document_permission import DocumentPermission  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.rag.ingestion import COLLECTION_NAME, ingest_document  # noqa: E402
from app.security.password import hash_password  # noqa: E402

PASSWORD = "correct-horse-battery"

HANDBOOK = (
    "Employee Handbook. Work from home policy: employees can work from home up to "
    "2 days per week, subject to manager approval and team requirements. "
    "Leave policy: employees receive 24 days of paid leave per year."
)
SALARY = (
    "Confidential Salary Report. Salary bands for employees: engineers earn between "
    "80000 and 120000 per year. Salary of the employees in the company is reviewed "
    "annually by the compensation committee."
)


@pytest.fixture()
def world():
    """Fresh DB + vector store with two tenants and a small document set."""
    try:
        _memory_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    LLM_CALLS.clear()

    db = SessionLocal()
    db.add_all([Tenant(name="Acme Industries", slug="acme"), Tenant(name="Globex", slug="globex")])
    db.commit()

    def user(email, name, role, tenant="acme"):
        u = User(email=email, full_name=name, password_hash=hash_password(PASSWORD), role=role, tenant_id=tenant)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    ids = {
        "admin": user("admin@acme.test", "Jane Admin", "Admin").id,
        "manager": user("mark@acme.test", "Mark Manager", "Manager").id,
        "employee": user("emma@acme.test", "Emma Employee", "Employee").id,
        "other_employee": user("eli@acme.test", "Eli Employee", "Employee").id,
        "globex_admin": user("root@globex.test", "Gina Globex", "Admin", "globex").id,
    }

    handbook = Document(title="Employee Handbook", file_name="Employee_Handbook.pdf", content=HANDBOOK, tenant_id="acme", classification="Internal")
    salary = Document(title="Salary Report", file_name="Salary_Report.pdf", content=SALARY, tenant_id="acme", classification="Confidential")
    db.add_all([handbook, salary])
    db.commit()
    db.add(DocumentPermission(document_id=handbook.id, role="Employee", permission="read"))
    db.add(DocumentPermission(document_id=handbook.id, role="Manager", permission="read"))
    db.add(DocumentPermission(document_id=salary.id, role="Manager", permission="read"))
    db.commit()
    ingest_document(db, handbook)
    ingest_document(db, salary)
    ids["handbook"], ids["salary"] = handbook.id, salary.id
    db.close()
    return ids


@pytest.fixture()
def client(world):
    return TestClient(app)


@pytest.fixture()
def login(client):
    def _login(email):
        response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture()
def llm_calls():
    return LLM_CALLS
