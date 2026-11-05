"""Short hostile chats must not hide direct abuse or informal threat spellings."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.analysis import AnalyzeRequest, ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine


CONVERSATION = "Alice: you motherfucking moron\nBob: ill kill you\nAlice: fuck you bitch"


@pytest.fixture(scope="module")
def engine():
    return ContextGuardAnalysisEngine()


def test_exact_reported_conversation_is_critical(engine):
    result = engine.analyze(AnalyzeRequest(conversation=CONVERSATION))
    assert result.overall_risk == "Critical"
    assert result.risk_score >= 90
    assert result.metrics.threat_count == 1
    assert [message.classification for message in result.messages] == [
        "Potentially Harmful", "Threat / Urgent Concern", "Potentially Harmful",
    ]
    assert result.messages[1].target == "Alice"
    assert result.messages[1].signals.has_threat_lexicon
    assert all(not message.signals.is_sarcasm_suspect for message in result.messages)


@pytest.mark.parametrize("phrase", [
    "ill kill you", "ILL KILL U!!!", "I'll kill you", "I’ll kill you",
    "I will kill you", "im gonna hurt you", "im going to stab you",
    "I am going to shoot you", "imma kill u",
])
def test_common_direct_threat_spellings(engine, phrase):
    result = engine.analyze(AnalyzeRequest(conversation=f"Bob: {phrase}"))
    assert result.messages[0].classification == "Threat / Urgent Concern"
    assert result.overall_risk == "Critical"


@pytest.mark.parametrize("phrase", ["you motherfucking moron", "fuck you bitch", "fuck you", "you are a complete idiot"])
def test_short_direct_abuse_is_not_dismissed_as_ambiguous(engine, phrase):
    result = engine.analyze(AnalyzeRequest(conversation=f"Alice: {phrase}"))
    assert result.messages[0].classification == "Potentially Harmful"
    assert result.overall_risk == "Moderate"
    assert not result.messages[0].signals.is_sarcasm_suspect


@pytest.mark.parametrize("phrase", [
    "I will not kill you", "I won't kill you", "I am ill, can you help?",
    "This fucking printer is broken", "I will call you tomorrow",
])
def test_negation_illness_and_general_profanity_are_not_direct_threats(engine, phrase):
    result = engine.analyze(AnalyzeRequest(conversation=f"Bob: {phrase}"))
    assert result.metrics.threat_count == 0
    assert result.overall_risk != "Critical"


def test_friendship_and_emojis_do_not_suppress_a_death_threat(engine):
    result = engine.analyze(AnalyzeRequest(
        conversation="Alice: haha 😂\nBob: ill kill you 😂\nAlice: lol",
        context=ContextInfo(relationship="Close friends"),
    ))
    assert result.overall_risk == "Critical"
    assert result.messages[1].classification == "Threat / Urgent Concern"


def test_api_reports_the_critical_result():
    with TestClient(app) as client:
        response = client.post("/api/analyze", json={"conversation": CONVERSATION})
    assert response.status_code == 200
    assert response.json()["overall_risk"] == "Critical"
    assert response.json()["risk_score"] >= 90
