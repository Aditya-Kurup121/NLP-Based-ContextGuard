from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.analysis import AnalyzeRequest
from backend.app.services.engine import ContextGuardAnalysisEngine
from backend.app.services.nlp import linguistic_model

client = TestClient(app)


def test_hmm_endpoint_tags_repeated_words_by_position():
    # "can" is a verb then a noun; text-keyed lookup gave both the same spaCy tag.
    res = client.post("/api/nlp/hmm/tag", json={"text": "I can open the can."})
    assert res.status_code == 200
    data = res.json()
    assert len(data["comparison"]) == len(data["tokens"]) == 6
    if linguistic_model() is not None:
        spacy_tags = [row["spacy_pos"] for row in data["comparison"]]
        assert spacy_tags[1] in ("AUX", "VERB")
        assert spacy_tags[4] == "NOUN"


def test_custom_word2vec_does_not_replace_default_model():
    default_before = client.get("/api/nlp/word2vec/status").json()["vocabulary_size"]
    trained = client.post(
        "/api/nlp/word2vec/train",
        json={"corpus": ["apple banana cherry", "banana cherry apple"], "epochs": 5},
    ).json()
    model_id = trained["model_id"]
    assert trained["vocabulary_size"] == 3

    # Default model is unchanged for everyone else.
    assert client.get("/api/nlp/word2vec/status").json()["vocabulary_size"] == default_before
    assert client.post("/api/nlp/word2vec/vector", json={"word": "apple"}).status_code == 404

    # The custom model is reachable by its id.
    res = client.post("/api/nlp/word2vec/vector", json={"word": "apple", "model_id": model_id})
    assert res.status_code == 200

    # Unknown ids give a clear 404.
    res = client.post("/api/nlp/word2vec/vector", json={"word": "apple", "model_id": "missing"})
    assert res.status_code == 404


def test_playful_challenge_banter_without_hardcoded_words():
    engine = ContextGuardAnalysisEngine()
    result = engine.analyze(AnalyzeRequest(conversation=(
        "Leo: haha you got lucky 😂\n"
        "Kai: lol run it back then\n"
        "Leo: bring it on, round two"
    )))
    assert result.overall_risk == "Low"


def test_cors_allows_only_configured_origins():
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    blocked = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in blocked.headers
