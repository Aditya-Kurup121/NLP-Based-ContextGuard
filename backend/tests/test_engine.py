import pytest
from backend.app.schemas.analysis import AnalyzeRequest, ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine

@pytest.fixture
def engine():
    return ContextGuardAnalysisEngine()

def test_friendly_banter(engine):
    req = AnalyzeRequest(
        conversation=(
            "Alice: You're such a genius 😂\n"
            "Bob: Bro, I know. Nobel Prize incoming.\n"
            "Alice: Don't forget us when you're famous."
        ),
        context=ContextInfo(relationship="Close friends", setting="Group chat")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "Low"
    assert res.metrics.friendly_banter_count >= 1
    # Check that it's NOT flagged as cyberbullying
    assert res.metrics.threat_count == 0
    assert not any(m.classification == "Possible Cyberbullying" for m in res.messages)

def test_repeated_exclusion(engine):
    req = AnalyzeRequest(
        conversation=(
            "Alex: Nobody wants you in this group.\n"
            "Alex: Seriously, just leave.\n"
            "Alex: Everyone here would be happier without you."
        ),
        context=ContextInfo(relationship="Classmates", setting="Group chat")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "High"
    assert res.metrics.potentially_harmful_count >= 2
    # Alex is repeatedly targeting with exclusion
    assert any("Social Exclusion" in m.detected_pattern for m in res.messages)
    # No recipient is named or speaks in this transcript. Detect exclusion but
    # do not fabricate a participant merely to populate the targeting matrix.
    assert all(message.target is None for message in res.messages)
    assert res.targeting_patterns == []

def test_sarcasm_and_ambiguity(engine):
    req = AnalyzeRequest(
        conversation=(
            "Sam: Wow, you're a real genius.\n"
            "Jordan: What is that supposed to mean?\n"
            "Sam: Forget it."
        ),
        context=ContextInfo(relationship="Acquaintances", setting="Forum")
    )
    res = engine.analyze(req)
    # The system should recognize ambiguity or potential harm without automatically crying high-risk cyberbullying
    assert res.overall_risk in ["Low", "Moderate"]
    has_uncertain_or_potential = any(
        m.classification in ["Potentially Harmful", "Uncertain — More Context Needed"] 
        for m in res.messages
    )
    assert has_uncertain_or_potential
    # Ensure explanation clarifies that intent is ambiguous
    first_msg = res.messages[0]
    assert "genius" in first_msg.text.lower()
    assert first_msg.alternative_interpretation is not None

def test_threatening_language(engine):
    req = AnalyzeRequest(
        conversation="Taylor: I'm going to find you after class and hurt you.",
        context=ContextInfo(relationship="Peers", setting="Direct message")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "Critical"
    assert res.metrics.threat_count == 1
    assert res.messages[0].classification == "Threat / Urgent Concern"
    assert "safeguard" in res.recommendations[2].lower() or "safety" in res.recommendations[0].lower()
