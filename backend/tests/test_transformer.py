import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import transformer
from backend.training.train_transformer import best_threshold

client = TestClient(app)


def test_threshold_is_chosen_to_maximise_macro_f1():
    import numpy as np
    labels = [0, 0, 0, 1, 1]
    probabilities = np.array([0.1, 0.2, 0.3, 0.35, 0.9])
    # Any threshold in (0.30, 0.35] separates the classes perfectly; 0.5 does not.
    assert 0.3 < best_threshold(probabilities, labels) <= 0.35


def test_missing_model_degrades_gracefully(monkeypatch, tmp_path):
    monkeypatch.setattr(transformer, "MODEL_DIR", tmp_path / "absent")
    transformer.transformer_model.cache_clear()
    try:
        assert transformer.classify_texts_transformer(["hello", "you idiot"]) == [None, None]
        assert transformer.transformer_status() == {"loaded": False}
        res = client.post("/api/analyze", json={"conversation": "A: hi\nB: hello"})
        assert res.status_code == 200
        assert all(m["transformer_assessment"] is None for m in res.json()["messages"])
    finally:
        transformer.transformer_model.cache_clear()


@pytest.mark.skipif(transformer.transformer_model() is None, reason="Fine-tuned transformer not trained/installed")
def test_trained_transformer_scores_messages():
    scores = transformer.classify_texts_transformer(["Thanks for the help with the notes!", "Shut up you worthless idiot"])
    assert scores[0]["label"] == "not toxic"
    assert scores[1]["label"] == "toxic"
    assert scores[1]["toxicity_score"] > scores[0]["toxicity_score"]
    res = client.post("/api/analyze", json={"conversation": "A: you are a worthless idiot\nB: please stop"})
    assert res.json()["messages"][0]["transformer_assessment"]["label"] == "toxic"
    assert client.get("/api/nlp/status").json()["local_transformer_loaded"] is True
