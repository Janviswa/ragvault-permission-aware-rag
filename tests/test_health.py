from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint_responds():
    r = TestClient(app).get("/health")
    assert r.status_code == 200 and r.json()["api"] == "ok"
