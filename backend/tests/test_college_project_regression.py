"""
ContextGuard Regression Test — 15-Turn College Project Conversation
===================================================================
Verifies:
1. Rohan is identified as the primary aggressor.
2. Aarav is identified as the primary target.
3. Karan is recognized as a bystander defender.
4. Turn 4 is not neutral (recognized as personal degradation and exclusion).
5. Turn 7 is recognized as a boundary/protest signal.
6. Turn 8 is recognized as social exclusion.
7. Turn 9 contributes evidence of repeated exclusion.
8. Turn 10 is recognized as personal degradation.
9. Turn 11 is recognized as defender intervention.
10. Turn 12 is recognized as retaliatory intimidation.
11. Turn 13 contributes to victim distress assessment (not aggression).
12. Turn 15 is recognized as continued exclusion.
13. Overall synthesis recognizes repeated asymmetric targeting pattern.

Separate tests:
- Friendly mutual banter remains low risk.
- Legitimate criticism is not classified as bullying.
- A single insult is not automatically classified as a physical threat.
- Bystander defense is not misclassified.
- A single expression of distress does not automatically imply bullying.
"""

import pytest
from backend.app.schemas.analysis import AnalyzeRequest, ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine
from backend.app.services.parser import parse_conversation
from backend.app.services.features import extract_all_features, infer_message_targets


COLLEGE_PROJECT_CONV = (
    "Aarav: Guys, are we creating a group for the college project?\n"
    "Rohan: Already created one. Everyone important is there.\n"
    "Aarav: What about me? I'm part of the project too.\n"
    "Rohan: We thought it would be easier without you slowing everyone down.\n"
    "Karan: Bro, that's unnecessary. Aarav is literally assigned to our team.\n"
    "Rohan: Nobody asked you, Karan.\n"
    "Aarav: Can you stop making jokes about me? It's getting annoying.\n"
    "Rohan: Relax, nobody wants you out. We're just saying the group works better without you.\n"
    "Aarav: You have excluded me from every discussion this week. How am I supposed to contribute?\n"
    "Rohan: Maybe if you were actually useful, we'd include you.\n"
    "Karan: This isn't funny anymore. Add him to the group and share the project files.\n"
    "Rohan: Keep defending him. You'll both get ignored.\n"
    "Aarav: I genuinely don't want to come to college tomorrow because of this.\n"
    "Karan: Aarav, I'm sorry. I'll make sure you get the project material.\n"
    "Rohan: Do whatever you want. He's still not getting added to my group."
)

COLLEGE_CTX = ContextInfo(relationship="College Classmates", setting="Group Chat")


@pytest.fixture(scope="module")
def engine():
    return ContextGuardAnalysisEngine()


@pytest.fixture(scope="module")
def project_result(engine):
    req = AnalyzeRequest(conversation=COLLEGE_PROJECT_CONV, context=COLLEGE_CTX)
    return engine.analyze(req)


class TestCollegeProjectRegression:
    """Verifies all 13 points for the 15-turn college project cyberbullying dialogue."""

    def test_rohan_is_primary_aggressor(self, project_result):
        rohan_info = next(p for p in project_result.participants if p.name == "Rohan")
        assert rohan_info.harmful_sent >= 5, f"Rohan harmful_sent should be >= 5, got {rohan_info.harmful_sent}"
        assert "Primary source" in rohan_info.role_summary or "Frequent source" in rohan_info.role_summary

    def test_aarav_is_primary_target(self, project_result):
        aarav_info = next(p for p in project_result.participants if p.name == "Aarav")
        assert aarav_info.harmful_sent == 0, "Aarav should have 0 harmful sent"
        assert aarav_info.targeted_count >= 4, f"Aarav targeted_count should be >= 4, got {aarav_info.targeted_count}"
        assert "recipient" in aarav_info.role_summary.lower()

    def test_karan_is_bystander_defender(self, project_result):
        karan_info = next(p for p in project_result.participants if p.name == "Karan")
        assert karan_info.harmful_sent == 0, "Karan should have 0 harmful sent"
        assert "bystander" in karan_info.role_summary.lower() or "defender" in karan_info.role_summary.lower()

    def test_turn_4_is_not_neutral(self, project_result):
        # Rohan: "We thought it would be easier without you slowing everyone down."
        turn_4 = project_result.messages[3]
        assert turn_4.classification in ["Potentially Harmful", "Possible Cyberbullying"], (
            f"Turn 4 should be harmful, got {turn_4.classification}"
        )
        assert ("Degradation" in turn_4.detected_pattern or "Exclusion" in turn_4.detected_pattern), (
            f"Turn 4 pattern should indicate degradation or exclusion, got {turn_4.detected_pattern}"
        )

    def test_turn_7_is_boundary_protest(self, project_result):
        # Aarav: "Can you stop making jokes about me? It's getting annoying."
        turn_7 = project_result.messages[6]
        assert turn_7.signals.is_victim_protest, "Turn 7 should set is_victim_protest"
        assert "Stop Request" in turn_7.detected_pattern or "Boundary" in turn_7.detected_pattern or "Protest" in turn_7.detected_pattern

    def test_turn_8_is_social_exclusion(self, project_result):
        # Rohan: "Relax, nobody wants you out. We're just saying the group works better without you."
        turn_8 = project_result.messages[7]
        assert turn_8.classification in ["Possible Cyberbullying", "Potentially Harmful"]
        assert "Exclusion" in turn_8.detected_pattern

    def test_turn_9_contributes_evidence_of_repeated_exclusion(self, project_result):
        # Aarav: "You have excluded me from every discussion this week. How am I supposed to contribute?"
        turn_9 = project_result.messages[8]
        assert turn_9.signals.is_victim_protest, "Turn 9 should set is_victim_protest"
        assert "Exclusion" in turn_9.detected_pattern or "Protest" in turn_9.detected_pattern or "Grievance" in turn_9.detected_pattern
        assert turn_9.classification != "Possible Cyberbullying", "Victim reporting exclusion should not be flagged as bully"

    def test_turn_10_is_personal_degradation(self, project_result):
        # Rohan: "Maybe if you were actually useful, we'd include you."
        turn_10 = project_result.messages[9]
        assert turn_10.classification in ["Possible Cyberbullying", "Potentially Harmful"]
        assert ("Degradation" in turn_10.detected_pattern or "Exclusion" in turn_10.detected_pattern or "Belittling" in turn_10.detected_pattern)

    def test_turn_11_is_defender_intervention(self, project_result):
        # Karan: "This isn't funny anymore. Add him to the group and share the project files."
        turn_11 = project_result.messages[10]
        assert turn_11.classification == "Harmless / Neutral"
        assert "Bystander Defence" in turn_11.detected_pattern or "Supportive Intervention" in turn_11.detected_pattern

    def test_turn_12_is_retaliatory_intimidation(self, project_result):
        # Rohan: "Keep defending him. You'll both get ignored."
        turn_12 = project_result.messages[11]
        assert turn_12.classification in ["Potentially Harmful", "Possible Cyberbullying"]
        assert ("Retaliatory" in turn_12.detected_pattern or "Intimidation" in turn_12.detected_pattern or "Defender" in turn_12.detected_pattern)
        assert turn_12.signals.is_retaliatory_threat or turn_12.signals.has_intimidation

    def test_turn_13_is_victim_distress(self, project_result):
        # Aarav: "I genuinely don't want to come to college tomorrow because of this."
        turn_13 = project_result.messages[12]
        assert turn_13.signals.is_victim_protest or turn_13.signals.has_distress
        assert turn_13.classification != "Possible Cyberbullying", "Victim distress should not be classified as aggression"
        assert "Distress" in turn_13.detected_pattern or "Avoidance" in turn_13.detected_pattern or "Protest" in turn_13.detected_pattern

    def test_turn_15_is_continued_exclusion(self, project_result):
        # Rohan: "Do whatever you want. He's still not getting added to my group."
        turn_15 = project_result.messages[14]
        assert turn_15.classification in ["Possible Cyberbullying", "Potentially Harmful"]
        assert "Exclusion" in turn_15.detected_pattern

    def test_overall_risk_is_high_with_repeated_targeting(self, project_result):
        assert project_result.overall_risk == "High", f"Expected High risk, got {project_result.overall_risk}"
        assert project_result.risk_score >= 75.0, f"Expected risk score >= 75, got {project_result.risk_score}"
        summary = project_result.conversation_summary
        assert "repeated" in summary.lower() or "asymmetric" in summary.lower()
        assert "rohan" in summary.lower()
        assert "aarav" in summary.lower()


class TestBoundaryCasesAndCounterexamples:
    """Verifies that counterexamples and benign cases remain safely calibrated."""

    def test_friendly_mutual_banter_remains_low_risk(self, engine):
        conv = (
            "Alex: You're such a clown haha 😂\n"
            "Jordan: Bro you literally missed an empty net lmao 💀\n"
            "Alex: Rematch right now loser 🤣\n"
            "Jordan: Anytime bro haha"
        )
        res = engine.analyze(AnalyzeRequest(conversation=conv, context=ContextInfo(relationship="Close Friends")))
        assert res.overall_risk == "Low", f"Friendly banter should be Low risk, got {res.overall_risk}"
        assert res.risk_score < 30.0

    def test_legitimate_criticism_not_classified_as_bullying(self, engine):
        conv = (
            "Lead: The pull request fails unit tests on module A and lacks documentation.\n"
            "Dev: I will review the test logs and update the docstrings.\n"
            "Lead: Please make sure the lint checks pass before merging tomorrow."
        )
        res = engine.analyze(AnalyzeRequest(conversation=conv, context=ContextInfo(relationship="Coworkers")))
        assert res.overall_risk == "Low", f"Legitimate critique should be Low risk, got {res.overall_risk}"
        assert res.metrics.potentially_harmful_count == 0

    def test_single_insult_not_automatically_physical_threat(self, engine):
        conv = (
            "Sam: That was a dumb mistake.\n"
            "Jordan: Yeah, my bad."
        )
        res = engine.analyze(AnalyzeRequest(conversation=conv))
        assert res.overall_risk in ["Low", "Moderate"]
        assert res.metrics.threat_count == 0, "Single tease/insult must not be classified as a physical threat"

    def test_bystander_defense_not_misclassified_as_aggression(self, engine):
        conv = (
            "Alice: That is completely unfair. Sam has worked just as hard as anyone else on this assignment.\n"
            "Bob: Fine, whatever."
        )
        res = engine.analyze(AnalyzeRequest(conversation=conv))
        alice_msg = res.messages[0]
        assert alice_msg.classification == "Harmless / Neutral", f"Bystander defense should be neutral, got {alice_msg.classification}"
        assert "Bystander" in alice_msg.detected_pattern or "Supportive" in alice_msg.detected_pattern

    def test_single_expression_of_distress_does_not_imply_bullying(self, engine):
        conv = (
            "Chris: I'm feeling so anxious about exams tomorrow, I don't want to come to college.\n"
            "Pat: Take a deep breath Chris, we've studied together, you'll be fine."
        )
        res = engine.analyze(AnalyzeRequest(conversation=conv, context=ContextInfo(relationship="Classmates")))
        assert res.overall_risk in ["Low", "Moderate"]
        # Chris's distress should not be classified as bullying
        chris_msg = res.messages[0]
        assert chris_msg.classification != "Possible Cyberbullying"
        assert chris_msg.classification != "Threat / Urgent Concern"

