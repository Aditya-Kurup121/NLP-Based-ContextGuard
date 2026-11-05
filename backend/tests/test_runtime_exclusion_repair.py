"""
Runtime Verification and Regression Test Suite for Workplace Exclusion & Bystander Defense
========================================================================================
Validates that:
1. Multi-turn covert/indirect exclusion, defender challenge, boundary dismissal,
   and overt meeting ostracism are correctly detected and aggregated as HIGH RISK.
2. Bystander interventions ("That's unnecessary", "Leave Sam alone") are classified
   as pro-social Harmless / Neutral with clear bystander contextual evidence.
3. Aggressor pushback against defenders ("Why are you always taking Sam's side?")
   is classified as Potentially Harmful (Defender Challenge / Bystander Silencing).
4. Sarcasm, neutral disagreements, and friendly banter remain accurately calibrated.
5. Guardrail: Interactions containing bystander defense or explicit stop requests
   are NEVER silently collapsed to "LOW RISK / SAFE INTERACTION".
"""

import pytest
from backend.app.schemas.analysis import AnalyzeRequest, ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine
from fastapi.testclient import TestClient
from backend.app.main import app

WORKPLACE_EXCLUSION_CONV = (
    "Sam: Can someone explain why I wasn't added to the project meeting?\n"
    "Jordan: Maybe because meetings go better when certain people aren't there.\n"
    "Sam: What do you mean by that?\n"
    "Jordan: Nothing, just saying the team works more efficiently without distractions.\n"
    "Alex: That's unnecessary, Sam has done a lot of work on this project.\n"
    "Jordan: Why are you always taking Sam's side?\n"
    "Sam: I've asked you before to stop making personal comments about me.\n"
    "Jordan: I'm not making personal comments. I'm just telling the truth.\n"
    "Jordan: Anyway, don't expect an invitation to the next meeting either.\n"
    "Alex: Jordan, leave Sam alone and send the meeting details.\n"
    "Jordan: Fine, I'll send them. Can we move on now?\n"
    "Sam: I just want to be included in the project discussions."
)

WORKPLACE_CTX = ContextInfo(relationship="Coworkers", setting="Project Chat")


@pytest.fixture(scope="module")
def engine():
    return ContextGuardAnalysisEngine()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestWorkplaceExclusionRuntime:
    """Verifies that the live pipeline correctly assesses the 12-turn workplace exclusion dialogue."""

    @pytest.fixture(scope="class")
    def result(self, engine):
        req = AnalyzeRequest(conversation=WORKPLACE_EXCLUSION_CONV, context=WORKPLACE_CTX)
        return engine.analyze(req)

    def test_overall_risk_is_high(self, result):
        assert result.overall_risk == "High", f"Expected High, got {result.overall_risk}"

    def test_risk_score_in_high_range(self, result):
        assert 75.0 <= result.risk_score <= 89.0, f"Expected 75-89, got {result.risk_score}"

    def test_harmful_messages_count_at_least_four(self, result):
        assert result.metrics.potentially_harmful_count >= 4, (
            f"Expected at least 4 harmful turns, got {result.metrics.potentially_harmful_count}"
        )

    def test_turn_2_covert_exclusion(self, result):
        msg = result.messages[1]
        assert msg.speaker == "Jordan"
        assert msg.classification == "Potentially Harmful"
        assert "Indirect / Covert Social Exclusion" in msg.detected_pattern

    def test_turn_4_repeated_exclusion(self, result):
        msg = result.messages[3]
        assert msg.speaker == "Jordan"
        assert msg.classification in ["Possible Cyberbullying", "Potentially Harmful"]
        assert any("distraction" in e.lower() or "exclusion" in e.lower() for e in msg.contextual_evidence)

    def test_turn_5_bystander_defense(self, result):
        msg = result.messages[4]
        assert msg.speaker == "Alex"
        assert msg.classification == "Harmless / Neutral"
        assert "Bystander Defence" in msg.detected_pattern

    def test_turn_6_defender_challenge(self, result):
        msg = result.messages[5]
        assert msg.speaker == "Jordan"
        assert msg.classification == "Potentially Harmful"
        assert "Defender Challenge" in msg.detected_pattern

    def test_turn_7_victim_stop_request(self, result):
        msg = result.messages[6]
        assert msg.speaker == "Sam"
        assert msg.classification == "Uncertain — More Context Needed"
        assert "Explicit Stop Request" in msg.detected_pattern

    def test_turn_8_dismissive_gaslighting(self, result):
        msg = result.messages[7]
        assert msg.speaker == "Jordan"
        assert msg.classification == "Potentially Harmful"
        assert "Boundary Invalidation" in msg.detected_pattern

    def test_turn_9_overt_meeting_exclusion(self, result):
        msg = result.messages[8]
        assert msg.speaker == "Jordan"
        assert msg.classification == "Possible Cyberbullying"
        assert "Repeated Social Exclusion" in msg.detected_pattern

    def test_turn_10_alex_bystander_defense(self, result):
        msg = result.messages[9]
        assert msg.speaker == "Alex"
        assert msg.classification == "Harmless / Neutral"
        assert "Bystander Defence" in msg.detected_pattern

    def test_targeting_matrix_shows_jordan_asymmetric_aggressor(self, result):
        jordan_info = next(p for p in result.participants if p.name == "Jordan")
        sam_info = next(p for p in result.participants if p.name == "Sam")
        assert jordan_info.harmful_sent >= 4
        assert sam_info.harmful_sent == 0
        assert sam_info.targeted_count >= 3


class TestApiIntegrationWorkplaceExclusion:
    """Verifies that the actual FastAPI HTTP endpoint returns the repaired assessment."""

    def test_api_returns_high_risk(self, client):
        payload = {
            "conversation": WORKPLACE_EXCLUSION_CONV,
            "context": {"relationship": "Coworkers", "setting": "Project Chat"}
        }
        resp = client.post("/api/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_risk"] == "High"
        assert data["risk_score"] >= 75.0
        assert data["metrics"]["potentially_harmful_count"] >= 4
        assert "cyberbullying" in data["conversation_summary"].lower()


class TestSilentIgnoralGuardrail:
    """Ensures that protest and bystander signals are NEVER silently ignored into 'Low Risk / Safe Interaction'."""

    def test_bystander_defense_with_unresolved_tension_is_not_low_safe(self, engine):
        conv = (
            "Alex: Jordan, come on, that's unnecessary. Leave Sam alone.\n"
            "Jordan: Mind your own business."
        )
        req = AnalyzeRequest(conversation=conv, context=ContextInfo(relationship="Peers", setting="Group chat"))
        res = engine.analyze(req)
        # Must not be Low Risk / Safe Interaction
        assert res.overall_risk in ["Moderate", "High"]
        assert "Routine, neutral communication" not in res.conversation_summary

    def test_explicit_stop_request_without_banter_is_not_low_safe(self, engine):
        conv = (
            "Jordan: You're always making mistakes.\n"
            "Sam: I'm asking you to stop making personal comments about me."
        )
        req = AnalyzeRequest(conversation=conv, context=ContextInfo(relationship="Coworkers", setting="Direct chat"))
        res = engine.analyze(req)
        assert res.overall_risk in ["Moderate", "High"]


class TestNonBullyingCounterexamples:
    """Ensures that valid benign conflict, task discussions, and banter are NOT over-flagged."""

    def test_constructive_technical_disagreement_stays_low(self, engine):
        conv = (
            "David: I don't agree with using MongoDB here, PostgreSQL handles relational joins much better.\n"
            "Sarah: I understand your point, but Mongo allows faster prototyping for our unstructured documents.\n"
            "David: Fair enough, let's schedule 15 minutes to compare schema migration costs."
        )
        req = AnalyzeRequest(conversation=conv, context=ContextInfo(relationship="Coworkers", setting="Slack"))
        res = engine.analyze(req)
        assert res.overall_risk == "Low"
        assert res.metrics.potentially_harmful_count == 0

    def test_friendly_gaming_banter_stays_low(self, engine):
        conv = (
            "Leo: Nice shot pro player 😂\n"
            "Kai: Lmao thanks, 1v1 rematch right now loser haha\n"
            "Leo: In your dreams bro let's go!"
        )
        req = AnalyzeRequest(conversation=conv, context=ContextInfo(relationship="Friends", setting="Discord"))
        res = engine.analyze(req)
        assert res.overall_risk == "Low"
        assert res.metrics.friendly_banter_count >= 1
        assert res.metrics.potentially_harmful_count == 0
