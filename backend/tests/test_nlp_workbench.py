import json
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy.sparse import csr_matrix
from sklearn.naive_bayes import MultinomialNB

from backend.app.main import app
from backend.app.services import hosted, nlp
from backend.training.manual_nb import ManualMultinomialNB
from backend.training.train import fingerprint, read_unique


def test_manual_nb_matches_reference_posterior():
    X = csr_matrix([[4, 0, 1], [3, 0, 0], [0, 5, 1], [0, 3, 0]])
    y = [0, 0, 1, 1]
    queries = csr_matrix([[1, 0, 0], [0, 2, 1], [0, 0, 0]])
    manual = ManualMultinomialNB().fit(X, y)
    reference = MultinomialNB().fit(X, y)
    assert np.allclose(manual.predict_proba(queries), reference.predict_proba(queries))
    assert list(manual.predict(queries)) == list(reference.predict(queries))


def test_manual_tfidf_uses_document_frequency_not_total_frequency():
    result = nlp.manual_vectorization(["cat cat dog", "dog"])
    assert result["vocabulary"] == ["cat", "dog"]
    assert result["bow"] == [[2, 1], [0, 1]]
    assert result["tfidf"][0][0] == round(2 * (math.log(3 / 2) + 1), 5)
    assert result["tfidf"][0][1] == 1


def test_normalization_preserves_negation_emojis_and_case_for_original():
    result = nlp.normalize("I am NOT angry 😂! https://example.com a@b.com")
    assert "not" in result and "😂!" in result
    assert "url" in result and "email" in result
    assert "example.com" not in result


def test_conflicting_duplicates_excluded(tmp_path):
    path = tmp_path / "train.jsonl"
    path.write_text('\n'.join(json.dumps(row) for row in [
        {"text": "Hello world", "label": 0}, {"text": "HELLO   world", "label": 1},
        {"text": "independent example", "label": 0},
    ]), encoding="utf-8")
    rows = read_unique(path)
    assert fingerprint("Hello world") not in rows
    assert len(rows) == 1


def test_inspect_validation_and_vectorization_limits():
    with TestClient(app) as client:
        assert client.post("/api/nlp/inspect", json={"text": " "}).status_code == 400
        assert client.post("/api/nlp/inspect", json={"text": "x" * 5001}).status_code == 422
        assert client.post("/api/nlp/vectorize", json={"documents": [""]}).status_code == 400
        assert client.post("/api/nlp/vectorize", json={"documents": ["a"] * 6}).status_code == 422


def test_hosted_requires_explicit_consent_and_configuration(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HF_CHAT_MODEL", raising=False)
    with TestClient(app) as client:
        assert client.post("/api/nlp/hosted-review", json={"conversation": "Alex: Hello"}).status_code == 422
        assert client.post("/api/nlp/hosted-review", json={"conversation": "Alex: Hello", "consent_to_external_processing": False}).status_code == 422
        assert client.post("/api/nlp/hosted-review", json={"conversation": "Alex: Hello", "consent_to_external_processing": True}).status_code == 503


@pytest.mark.parametrize("quote,valid", [("Please stop", True), ("Invented threat", False)])
def test_hosted_rejects_fabricated_evidence(monkeypatch, quote, valid):
    monkeypatch.setenv("HF_TOKEN", "test-secret-not-real")
    monkeypatch.setenv("HF_CHAT_MODEL", "test/model")
    content = {"risk": "Uncertain", "summary": "Needs context.", "evidence": [{"quote": quote, "explanation": "A request."}], "alternative_interpretation": "Could be a boundary.", "suggested_action": "Read the replies."}
    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(content)}}]}
    def post(self, url, **kwargs):
        assert url == "https://router.huggingface.co/v1/chat/completions"
        assert kwargs["json"]["messages"][0]["role"] == "system"
        return Response()
    monkeypatch.setattr(hosted.httpx.Client, "post", post)
    if valid:
        assert hosted.review_conversation("Alex: Please stop")["risk"] == "Uncertain"
    else:
        with pytest.raises(RuntimeError, match="invalid evidence"):
            hosted.review_conversation("Alex: Please stop")


def test_real_pos_ner_and_model_explanations_when_installed():
    if nlp.linguistic_model() is None or nlp.classifier() is None:
        pytest.skip("Run the documented model setup for the integration check.")
    text = "Maya works in Mumbai. Please do not tease her."
    with TestClient(app) as client:
        response = client.post("/api/nlp/inspect", json={"text": text})
        assert response.status_code == 200
        result = response.json()
        assert any(token["pos"] == "VERB" for token in result["tokens"])
        assert any(entity["text"] == "Mumbai" for entity in result["entities"])
        assert all(text[entity["start"]:entity["end"]] == entity["text"] for entity in result["entities"])
        assert "not" in result["stopword_filtered"]
        assert 0 <= result["classifier"]["toxicity_score"] <= 1
        assert result["classifier"]["top_features"]
        analysis = client.post("/api/analyze", json={"conversation": "Alex: Hello Maya.\nMaya: Hi Alex."}).json()
        assert all(message["statistical_assessment"] for message in analysis["messages"])
