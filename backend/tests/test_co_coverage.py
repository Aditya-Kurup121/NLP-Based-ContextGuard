"""Comprehensive tests verifying CO1, CO2, CO3, CO4 and CO5 endpoints and logic."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.levenshtein import compute_levenshtein
from backend.app.services.word2vec import EducationalWord2Vec, get_word2vec_model
from backend.app.services.hmm_tagger import HiddenMarkovModelTagger, get_hmm_tagger
from backend.app.services.nlp import clean_text_noise, normalize, inspect_text


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------
# CO1: Text Preprocessing & Cleaning
# ---------------------------------------------------------------------

def test_clean_text_noise():
    dirty = "Hello &amp; welcome! <script>alert(1)</script> \u200b\ufeff  How are you?   "
    cleaned = clean_text_noise(dirty)
    assert "&" in cleaned
    assert "<script>" not in cleaned
    assert "\u200b" not in cleaned
    assert "  " not in cleaned


def test_inspect_text_co1_capabilities():
    text = "Maya told Jordan: 'Please do not tease me!' They met in Mumbai. Check https://example.com"
    res = inspect_text(text)
    assert "tokenization" in res
    assert "sentences" in res["tokenization"]
    assert len(res["tokenization"]["sentences"]) >= 2
    assert "stopword_analysis" in res
    assert "not" in [w.lower() for w in res["stopword_analysis"]["preserved_negations"]]
    assert "stemming" in res
    assert len(res["stemming"]["porter"]) > 0
    assert len(res["stemming"]["lancaster"]) > 0
    assert "hmm_pos_tagging" in res


# ---------------------------------------------------------------------
# CO2: Feature Extraction & Word Representations
# ---------------------------------------------------------------------

def test_levenshtein_distance():
    res = compute_levenshtein("kitten", "sitting")
    assert res["distance"] == 3
    assert res["similarity_ratio"] < 1.0
    assert len(res["operations"]) >= 6


def test_word2vec_training_and_similarity():
    w2v = get_word2vec_model()
    assert len(w2v.vocab) > 20
    vec = w2v.get_vector("friend")
    assert vec is not None
    assert len(vec) == 32
    sim = w2v.cosine_similarity("friend", "friends")
    assert sim is not None
    neighbors = w2v.nearest_neighbors("friend", top_n=3)
    assert len(neighbors) == 3


def test_word2vec_api_endpoints(client):
    res_status = client.get("/api/nlp/word2vec/status")
    assert res_status.status_code == 200
    assert res_status.json()["vocabulary_size"] > 0

    res_sim = client.post("/api/nlp/word2vec/similarity", json={"word1": "friend", "word2": "peer"})
    assert res_sim.status_code == 200
    assert "cosine_similarity" in res_sim.json()

    res_neighbors = client.post("/api/nlp/word2vec/similar", json={"word": "threat", "top_n": 4})
    assert res_neighbors.status_code == 200
    assert len(res_neighbors.json()["nearest_neighbors"]) <= 4


# ---------------------------------------------------------------------
# CO3: POS Tagging & NER
# ---------------------------------------------------------------------

def test_hmm_viterbi_tagger():
    hmm = get_hmm_tagger()
    tokens = ["the", "students", "played", "happily", "."]
    tags, score, trellis = hmm.viterbi(tokens)
    assert len(tags) == len(tokens)
    assert tags[0] == "DET"
    assert tags[1] == "NOUN"
    assert tags[2] == "VERB"
    assert tags[-1] == "."
    assert score < 0.0  # Log-likelihood is negative


def test_hmm_api_endpoint(client):
    res = client.post("/api/nlp/hmm/tag", json={"text": "Good friends respect each other."})
    assert res.status_code == 200
    data = res.json()
    assert "hmm_tags" in data
    assert "comparison" in data
    assert len(data["comparison"]) > 0


# ---------------------------------------------------------------------
# CO4 & CO5: Evaluation & Classifier API
# ---------------------------------------------------------------------

def test_classifier_loaded_in_nlp_status(client):
    res = client.get("/api/nlp/status")
    assert res.status_code == 200
    data = res.json()
    assert data["classifier_loaded"] is True
    assert data["word2vec_loaded"] is True
    assert data["hmm_tagger_loaded"] is True


def test_laughter_does_not_override_lethal_or_retaliatory_threat(client):
    # Aggressor adding laughter to a threat must not become Friendly Banter
    payload = {
        "conversation": "Bob: I'm going to kill you 😂"
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_risk"] == "Critical"
    assert data["messages"][0]["classification"] == "Threat / Urgent Concern"


def test_laughter_does_not_override_post_protest_abuse(client):
    payload = {
        "conversation": (
            "Sam: Please stop, that hurts.\n"
            "Jordan: You are a pathetic loser 😂"
        )
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Jordan's turn must NOT be friendly banter because Sam explicitly protested
    assert data["messages"][1]["classification"] != "Friendly Banter"
    assert data["messages"][1]["classification"] in ["Potentially Harmful", "Possible Cyberbullying"]


def test_verbal_abuse_vs_physical_threat_distinct_classifications(client):
    # Verbal abuse alone should be Potentially Harmful, not physical Threat
    res_abuse = client.post("/api/analyze", json={"conversation": "Alice: You complete idiot"})
    assert res_abuse.status_code == 200
    assert res_abuse.json()["messages"][0]["classification"] == "Potentially Harmful"

    # Physical threat should be Threat / Urgent Concern
    res_threat = client.post("/api/analyze", json={"conversation": "Bob: I will beat the shit out of you"})
    assert res_threat.status_code == 200
    assert res_threat.json()["messages"][0]["classification"] == "Threat / Urgent Concern"

