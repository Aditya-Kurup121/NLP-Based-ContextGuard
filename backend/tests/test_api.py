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
    assert data["overall_accuracy"] >= 0.90
    assert "confusion_matrix" in data

def test_api_analyze_13_turn_regression(client):
    ex_resp = client.get("/api/examples/multi-turn-targeting-13")
    assert ex_resp.status_code == 200
    ex_data = ex_resp.json()
    payload = {
        "conversation": ex_data["conversation"],
        "context": {
            "relationship": ex_data["relationship"],
            "setting": ex_data["setting"]
        }
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "High"
    assert data["risk_score"] >= 70.0
    assert data["metrics"]["potentially_harmful_count"] >= 4

def test_api_analyze_retaliatory_threat(client):
    ex_resp = client.get("/api/examples/retaliatory-threat")
    assert ex_resp.status_code == 200
    ex_data = ex_resp.json()
    payload = {
        "conversation": ex_data["conversation"],
        "context": {
            "relationship": ex_data["relationship"],
            "setting": ex_data["setting"]
        }
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "High"
    assert data["metrics"]["threat_count"] >= 2

def test_api_analyze_workplace_exclusion_regression(client):
    ex_resp = client.get("/api/examples/workplace-exclusion")
    assert ex_resp.status_code == 200
    ex_data = ex_resp.json()
    payload = {
        "conversation": ex_data["conversation"],
        "context": {
            "relationship": ex_data["relationship"],
            "setting": ex_data["setting"]
        }
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "High"
    assert data["risk_score"] >= 80.0
    assert data["metrics"]["potentially_harmful_count"] >= 4
    
    msgs = data["messages"]
    # Turn 2: Jordan covert exclusion
    assert msgs[1]["classification"] == "Potentially Harmful"
    assert "Indirect / Covert Social Exclusion" in msgs[1]["detected_pattern"]
    assert any("exclusionary" in ev.lower() for ev in msgs[1]["contextual_evidence"])
    
    # Turn 4: Jordan repeated covert exclusion
    assert msgs[3]["classification"] == "Possible Cyberbullying"
    assert "Repeated Social Exclusion" in msgs[3]["detected_pattern"]
    
    # Turn 5: Alex bystander defense
    assert msgs[4]["classification"] == "Harmless / Neutral"
    assert "Bystander Defence" in msgs[4]["detected_pattern"]
    
    # Turn 6: Jordan defender challenge
    assert msgs[5]["classification"] == "Potentially Harmful"
    assert "Defender Challenge" in msgs[5]["detected_pattern"]
    
    # Turn 7: Sam explicit stop request
    assert msgs[6]["classification"] == "Uncertain — More Context Needed"
    assert "Stop Request" in msgs[6]["detected_pattern"]
    
    # Turn 8: Jordan dismissive invalidation / gaslighting
    assert msgs[7]["classification"] == "Potentially Harmful"
    assert "Boundary Invalidation" in msgs[7]["detected_pattern"]
    
    # Turn 9: Jordan overt meeting exclusion
    assert msgs[8]["classification"] == "Possible Cyberbullying"
    assert "Repeated Social Exclusion" in msgs[8]["detected_pattern"]
    
    # Turn 10: Alex bystander defense
    assert msgs[9]["classification"] == "Harmless / Neutral"
    assert "Bystander Defence" in msgs[9]["detected_pattern"]

def test_api_counterexample_technical_disagreement(client):
    payload = {
        "conversation": (
            "David: I don't agree with using MongoDB here, PostgreSQL handles relational joins much better.\n"
            "Sarah: I understand your point, but Mongo allows faster prototyping for our unstructured documents.\n"
            "David: Fair enough, let's schedule 15 minutes to compare schema migration costs."
        ),
        "context": {"relationship": "Coworkers", "setting": "Slack"}
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "Low"
    assert data["metrics"]["potentially_harmful_count"] == 0
    assert all(m["classification"] == "Harmless / Neutral" for m in data["messages"])

def test_api_counterexample_gaming_banter(client):
    payload = {
        "conversation": (
            "Leo: Your aim is in the clouds bro haha 😂\n"
            "Kai: Lmao I sneezed chill, 1v1 rematch right now loser 😂\n"
            "Leo: Let's go!"
        ),
        "context": {"relationship": "Gaming Friends", "setting": "Discord"}
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] == "Low"
    assert data["metrics"]["friendly_banter_count"] >= 1
    assert data["metrics"]["potentially_harmful_count"] == 0


