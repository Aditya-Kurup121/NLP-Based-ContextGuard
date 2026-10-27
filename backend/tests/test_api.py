import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_api_examples(client):
    response = client.get("/api/examples")
    assert response.status_code == 200
    examples = response.json()
    assert len(examples) >= 4
    assert any(e["id"] == "friendly-banter" for e in examples)
    assert any(e["id"] == "repeated-exclusion" for e in examples)

def test_api_analyze_valid(client):
    payload = {
        "conversation": "Alice: You're such a genius 😂\nBob: Bro, I know.",
        "context": {
            "relationship": "Friends",
            "setting": "Group chat"
        }
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overall_risk" in data
    assert "messages" in data
    assert len(data["messages"]) == 2

def test_api_analyze_empty(client):
    payload = {"conversation": "   "}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 400

def test_api_model_info(client):
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "engine_name" in data
    assert "limitations" in data

def test_api_evaluate(client):
    response = client.get("/api/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert "overall_accuracy" in data
    assert "confusion_matrix" in data
