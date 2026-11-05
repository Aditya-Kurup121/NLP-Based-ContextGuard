"""
Regression Test Suite — ContextGuard Threat & Intimidation Detection
=====================================================================
Covers the 7 scenarios required by Task 6 of the bug-fix specification:

  A. Seven-message retaliatory-threat conversation (Nikhil & Vivek)
  B. Friendly banter between friends
  C. Isolated ambiguous statement — "You're going to regret that."
  D. Direct threat with explicit target and future confrontation
  E. Repeated social exclusion without physical threat
  F. Sarcastic comments about a coding mistake (no physical threat)
  G. Recipient sets a boundary; sender follows with intimidation

Each test asserts ONLY the contract specified in the task description.
No test hard-codes implementation details that could change in future refactors.
"""

import pytest
from backend.app.schemas.analysis import AnalyzeRequest, ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine


@pytest.fixture(scope="module")
def engine():
    """Single engine instance shared across all tests in this module."""
    return ContextGuardAnalysisEngine()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _msg_by_idx(res, idx: int):
    """Return the message at 0-based index idx."""
    return res.messages[idx]


# ---------------------------------------------------------------------------
# Scenario A — The exact 7-message Nikhil & Vivek conversation
# Expected: HIGH RISK, risk score in [80, 89]
# Turn-level expectations:
#   Turn 0 (Nikhil):  Harmless / Neutral
#   Turn 1 (Vivek):   Harmless / Neutral
#   Turn 2 (Nikhil):  Potentially Harmful  (retaliatory warning)
#   Turn 3 (Vivek):   Uncertain — More Context Needed  (clarification)
#   Turn 4 (Nikhil):  Threat / Urgent Concern  (in-person confrontation)
#   Turn 5 (Vivek):   Uncertain — More Context Needed  (boundary / fear)
#   Turn 6 (Nikhil):  Threat / Urgent Concern  (reinforced intimidation)
# ---------------------------------------------------------------------------

NIKHIL_VIVEK_CONVERSATION = (
    "Nikhil: Why did you report my account?\n"
    "Vivek: You kept sending me abusive messages. I reported them.\n"
    "Nikhil: You're going to regret doing that.\n"
    "Vivek: What does that mean?\n"
    "Nikhil: I'll find you after college tomorrow.\n"
    "Vivek: Don't come near me. I'm serious.\n"
    "Nikhil: You should be worried about tomorrow."
)


def test_scenario_a_overall_risk_is_high(engine):
    """Scenario A — overall risk must be HIGH, not LOW or MODERATE."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "High", (
        f"Expected HIGH risk for retaliatory-threat conversation, got '{res.overall_risk}'. "
        f"Risk score: {res.risk_score}, messages: {[m.classification for m in res.messages]}"
    )


def test_scenario_a_risk_score_range(engine):
    """Scenario A — risk score must be in the 80-89 range for HIGH tier."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    assert 79 < res.risk_score <= 89, (
        f"Expected risk score in [80, 89], got {res.risk_score}."
    )


def test_scenario_a_turn_0_harmless(engine):
    """Turn 0 — 'Why did you report my account?' should be Harmless / Neutral."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t0 = _msg_by_idx(res, 0)
    assert t0.classification == "Harmless / Neutral", (
        f"Turn 0 expected 'Harmless / Neutral', got '{t0.classification}'"
    )


def test_scenario_a_turn_1_harmless(engine):
    """Turn 1 — 'You kept sending me abusive messages. I reported them.' should be Harmless / Neutral."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t1 = _msg_by_idx(res, 1)
    assert t1.classification == "Harmless / Neutral", (
        f"Turn 1 expected 'Harmless / Neutral', got '{t1.classification}'"
    )


def test_scenario_a_turn_2_retaliatory_threat(engine):
    """Turn 2 — 'You're going to regret doing that.' should be Potentially Harmful."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t2 = _msg_by_idx(res, 2)
    assert t2.classification == "Potentially Harmful", (
        f"Turn 2 expected 'Potentially Harmful' (retaliatory), got '{t2.classification}'"
    )


def test_scenario_a_turn_3_uncertain_inquiry(engine):
    """Turn 3 — 'What does that mean?' should be Uncertain -- More Context Needed."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t3 = _msg_by_idx(res, 3)
    assert t3.classification == "Uncertain \u2014 More Context Needed", (
        f"Turn 3 expected 'Uncertain -- More Context Needed', got '{t3.classification}'"
    )


def test_scenario_a_turn_4_confrontation_threat(engine):
    """Turn 4 — 'I'll find you after college tomorrow.' should be Threat / Urgent Concern."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t4 = _msg_by_idx(res, 4)
    assert t4.classification == "Threat / Urgent Concern", (
        f"Turn 4 expected 'Threat / Urgent Concern' (in-person confrontation), got '{t4.classification}'"
    )


def test_scenario_a_turn_5_boundary_fear(engine):
    """Turn 5 — 'Don't come near me. I'm serious.' should be Uncertain -- More Context Needed (boundary/fear)."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t5 = _msg_by_idx(res, 5)
    assert t5.classification == "Uncertain \u2014 More Context Needed", (
        f"Turn 5 expected 'Uncertain -- More Context Needed' (boundary), got '{t5.classification}'"
    )


def test_scenario_a_turn_6_persistent_threat(engine):
    """Turn 6 — 'You should be worried about tomorrow.' should be Threat / Urgent Concern."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t6 = _msg_by_idx(res, 6)
    assert t6.classification == "Threat / Urgent Concern", (
        f"Turn 6 expected 'Threat / Urgent Concern' (persistent intimidation), got '{t6.classification}'"
    )


def test_scenario_a_threat_count_at_least_two(engine):
    """Scenario A — at least 2 turns must be classified as Threat / Urgent Concern."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    assert res.metrics.threat_count >= 2, (
        f"Expected >=2 threat turns, got {res.metrics.threat_count}"
    )


def test_scenario_a_turn4_evidence_references_context(engine):
    """Turn 4 contextual evidence should mention escalation or prior retaliatory context."""
    req = AnalyzeRequest(
        conversation=NIKHIL_VIVEK_CONVERSATION,
        context=ContextInfo(relationship="Classmates", setting="Direct message")
    )
    res = engine.analyze(req)
    t4 = _msg_by_idx(res, 4)
    evidence_text = " ".join(t4.contextual_evidence).lower()
    assert any(
        kw in evidence_text
        for kw in ["escalat", "retaliat", "prior", "confrontation", "report", "grievance", "college"]
    ), f"Turn 4 evidence should reference escalation context; got: {t4.contextual_evidence}"


# ---------------------------------------------------------------------------
# Scenario B — Friendly banter between friends
# Expected: LOW RISK, no unjustified threat escalation
# ---------------------------------------------------------------------------

def test_scenario_b_friendly_banter_is_low_risk(engine):
    """Scenario B — reciprocal banter must stay at LOW risk."""
    req = AnalyzeRequest(
        conversation=(
            "Priya: Haha you played horribly today\n"
            "Raj: Lmao bro I had food poisoning, give me a break\n"
            "Priya: Sure sure, Nobel Prize for worst excuses\n"
            "Raj: Rematch tomorrow and I'll destroy you lmao"
        ),
        context=ContextInfo(relationship="Close friends", setting="Group chat")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "Low", (
        f"Friendly banter should be LOW risk, got '{res.overall_risk}'"
    )


def test_scenario_b_no_threat_count(engine):
    """Scenario B — threat count must be 0."""
    req = AnalyzeRequest(
        conversation=(
            "Priya: Haha you played horribly today\n"
            "Raj: Lmao bro I had food poisoning, give me a break\n"
            "Priya: Sure sure, Nobel Prize for worst excuses\n"
            "Raj: Rematch tomorrow and I'll destroy you lmao"
        ),
        context=ContextInfo(relationship="Close friends", setting="Group chat")
    )
    res = engine.analyze(req)
    assert res.metrics.threat_count == 0, (
        f"Banter should produce 0 threats, got {res.metrics.threat_count}"
    )


def test_scenario_b_no_cyberbullying_classification(engine):
    """Scenario B — no turn should be classified as Possible Cyberbullying."""
    req = AnalyzeRequest(
        conversation=(
            "Priya: Haha you played horribly today\n"
            "Raj: Lmao bro I had food poisoning, give me a break\n"
            "Priya: Sure sure, Nobel Prize for worst excuses\n"
            "Raj: Rematch tomorrow and I'll destroy you lmao"
        ),
        context=ContextInfo(relationship="Close friends", setting="Group chat")
    )
    res = engine.analyze(req)
    assert not any(m.classification == "Possible Cyberbullying" for m in res.messages), (
        "Banter should not be labeled as Possible Cyberbullying"
    )


# ---------------------------------------------------------------------------
# Scenario C — Isolated ambiguous statement: "You're going to regret that."
# Expected: Uncertain — More Context Needed (not HIGH or CRITICAL)
# ---------------------------------------------------------------------------

def test_scenario_c_isolated_ambiguous_is_uncertain_or_potentially_harmful(engine):
    """Scenario C — isolated 'You're going to regret that.' must be uncertain, not an active threat."""
    req = AnalyzeRequest(
        conversation="Morgan: You're going to regret that.",
        context=ContextInfo(relationship="Unknown", setting="Unknown")
    )
    res = engine.analyze(req)
    msg = res.messages[0]
    assert msg.classification in ["Uncertain \u2014 More Context Needed", "Potentially Harmful"], (
        f"Isolated ambiguous statement should be Uncertain or Potentially Harmful; got '{msg.classification}'"
    )


def test_scenario_c_not_escalated_to_high(engine):
    """Scenario C — risk must not be HIGH or CRITICAL for one ambiguous line without context."""
    req = AnalyzeRequest(
        conversation="Morgan: You're going to regret that.",
        context=ContextInfo(relationship="Unknown", setting="Unknown")
    )
    res = engine.analyze(req)
    assert res.overall_risk not in ["High", "Critical"], (
        f"A single ambiguous statement must not trigger HIGH/CRITICAL risk; got '{res.overall_risk}'"
    )


# ---------------------------------------------------------------------------
# Scenario D — Direct threat with explicit target and future confrontation
# Expected: Threat / Urgent Concern, CRITICAL risk
# ---------------------------------------------------------------------------

def test_scenario_d_direct_lethal_threat_is_critical(engine):
    """Scenario D — explicit future confrontation + harm keywords must trigger CRITICAL."""
    req = AnalyzeRequest(
        conversation="Taylor: I'm going to find you after class and hurt you.",
        context=ContextInfo(relationship="School peers", setting="Direct message")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "Critical", (
        f"Explicit violent threat should be CRITICAL, got '{res.overall_risk}'"
    )
    assert res.messages[0].classification == "Threat / Urgent Concern"


def test_scenario_d_threat_count_is_one(engine):
    """Scenario D — threat_count must be exactly 1."""
    req = AnalyzeRequest(
        conversation="Taylor: I'm going to find you after class and hurt you.",
        context=ContextInfo(relationship="School peers", setting="Direct message")
    )
    res = engine.analyze(req)
    assert res.metrics.threat_count == 1


# ---------------------------------------------------------------------------
# Scenario E — Repeated exclusion without physical threat
# Expected: HIGH risk, cyberbullying detection still works
# ---------------------------------------------------------------------------

def test_scenario_e_repeated_exclusion_is_high_risk(engine):
    """Scenario E — systematic exclusion must remain HIGH risk."""
    req = AnalyzeRequest(
        conversation=(
            "Sam: Nobody wants you in this group.\n"
            "Sam: Seriously, just leave already.\n"
            "Sam: Everyone here would be happier without you."
        ),
        context=ContextInfo(relationship="Classmates", setting="Group chat")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "High", (
        f"Repeated exclusion should be HIGH risk, got '{res.overall_risk}'"
    )


def test_scenario_e_exclusion_pattern_detected(engine):
    """Scenario E — social exclusion pattern must be detected in at least one turn."""
    req = AnalyzeRequest(
        conversation=(
            "Sam: Nobody wants you in this group.\n"
            "Sam: Seriously, just leave already.\n"
            "Sam: Everyone here would be happier without you."
        ),
        context=ContextInfo(relationship="Classmates", setting="Group chat")
    )
    res = engine.analyze(req)
    assert any("Social Exclusion" in m.detected_pattern for m in res.messages), (
        "Exclusion pattern should appear in detected_pattern for at least one turn"
    )


def test_scenario_e_no_physical_threat_escalation(engine):
    """Scenario E — repeated exclusion without physical threats must NOT be CRITICAL."""
    req = AnalyzeRequest(
        conversation=(
            "Sam: Nobody wants you in this group.\n"
            "Sam: Seriously, just leave already.\n"
            "Sam: Everyone here would be happier without you."
        ),
        context=ContextInfo(relationship="Classmates", setting="Group chat")
    )
    res = engine.analyze(req)
    assert res.overall_risk != "Critical", (
        "Pure exclusion without physical threats should not be CRITICAL"
    )
    assert res.metrics.threat_count == 0, (
        "Exclusion messages should not produce threat classifications"
    )


# ---------------------------------------------------------------------------
# Scenario F — Sarcastic comments about a coding mistake
# Expected: Moderate or Low risk, no physical-threat classification
# ---------------------------------------------------------------------------

def test_scenario_f_coding_sarcasm_no_threat(engine):
    """Scenario F — sarcastic coding remarks must not trigger physical threat labels."""
    req = AnalyzeRequest(
        conversation=(
            "Sarah: Wow, a real genius at work your loop runs forever.\n"
            "David: What is that supposed to mean?\n"
            "Sarah: Forget it. Just fix the off-by-one error."
        ),
        context=ContextInfo(relationship="Co-workers", setting="Code review chat")
    )
    res = engine.analyze(req)
    assert res.metrics.threat_count == 0, (
        f"Sarcastic coding remarks should not produce threat_count > 0, got {res.metrics.threat_count}"
    )
    assert not any(m.classification == "Threat / Urgent Concern" for m in res.messages), (
        "No coding-sarcasm turn should be classified as 'Threat / Urgent Concern'"
    )


def test_scenario_f_coding_sarcasm_risk_not_high(engine):
    """Scenario F — sarcastic coding banter must be Moderate or Low, not High or Critical."""
    req = AnalyzeRequest(
        conversation=(
            "Sarah: Wow, a real genius at work your loop runs forever.\n"
            "David: What is that supposed to mean?\n"
            "Sarah: Forget it. Just fix the off-by-one error."
        ),
        context=ContextInfo(relationship="Co-workers", setting="Code review chat")
    )
    res = engine.analyze(req)
    assert res.overall_risk in ["Low", "Moderate"], (
        f"Coding sarcasm should be Low or Moderate risk, got '{res.overall_risk}'"
    )


def test_scenario_f_coding_sarcasm_has_ambiguity_or_potential(engine):
    """Scenario F — at least one turn should be flagged as ambiguous or potentially harmful (not ignored)."""
    req = AnalyzeRequest(
        conversation=(
            "Sarah: Wow, a real genius at work your loop runs forever.\n"
            "David: What is that supposed to mean?\n"
            "Sarah: Forget it. Just fix the off-by-one error."
        ),
        context=ContextInfo(relationship="Co-workers", setting="Code review chat")
    )
    res = engine.analyze(req)
    has_nuanced = any(
        m.classification in ["Potentially Harmful", "Uncertain \u2014 More Context Needed"]
        for m in res.messages
    )
    assert has_nuanced, (
        "At least one coding-sarcasm turn should be labeled as Potentially Harmful or Uncertain"
    )


# ---------------------------------------------------------------------------
# Scenario G — Recipient explicitly asks sender to stay away; sender responds with intimidation
# Expected: HIGH RISK, elevated threat concern
# ---------------------------------------------------------------------------

def test_scenario_g_boundary_plus_intimidation_is_high_risk(engine):
    """Scenario G — intimidating follow-up after explicit boundary must be HIGH risk."""
    req = AnalyzeRequest(
        conversation=(
            "Alex: I'm coming to your house whether you like it or not.\n"
            "Sam: Don't come near me. Stay away.\n"
            "Alex: You can't hide from me."
        ),
        context=ContextInfo(relationship="Acquaintances", setting="Direct message")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "High", (
        f"Boundary violation + further intimidation should be HIGH risk, got '{res.overall_risk}'"
    )


def test_scenario_g_intimidation_after_boundary_is_threat(engine):
    """Scenario G — 'You can't hide from me' after explicit boundary must be Threat / Urgent Concern."""
    req = AnalyzeRequest(
        conversation=(
            "Alex: I'm coming to your house whether you like it or not.\n"
            "Sam: Don't come near me. Stay away.\n"
            "Alex: You can't hide from me."
        ),
        context=ContextInfo(relationship="Acquaintances", setting="Direct message")
    )
    res = engine.analyze(req)
    t2 = _msg_by_idx(res, 2)
    assert t2.classification == "Threat / Urgent Concern", (
        f"Turn 2 ('You can't hide from me') should be 'Threat / Urgent Concern', got '{t2.classification}'"
    )


def test_scenario_g_boundary_turn_is_uncertain_or_harmful(engine):
    """Scenario G — Sam's boundary assertion should be recognized as Uncertain (fear/boundary indicator)."""
    req = AnalyzeRequest(
        conversation=(
            "Alex: I'm coming to your house whether you like it or not.\n"
            "Sam: Don't come near me. Stay away.\n"
            "Alex: You can't hide from me."
        ),
        context=ContextInfo(relationship="Acquaintances", setting="Direct message")
    )
    res = engine.analyze(req)
    t1 = _msg_by_idx(res, 1)
    assert t1.classification in ["Uncertain \u2014 More Context Needed", "Potentially Harmful"], (
        f"Boundary assertion should be Uncertain or Potentially Harmful, got '{t1.classification}'"
    )


def test_scenario_g_first_turn_is_confrontation_threat(engine):
    """Scenario G — 'I'm coming to your house' should be detected as a confrontation threat."""
    req = AnalyzeRequest(
        conversation=(
            "Alex: I'm coming to your house whether you like it or not.\n"
            "Sam: Don't come near me. Stay away.\n"
            "Alex: You can't hide from me."
        ),
        context=ContextInfo(relationship="Acquaintances", setting="Direct message")
    )
    res = engine.analyze(req)
    t0 = _msg_by_idx(res, 0)
    assert t0.classification == "Threat / Urgent Concern", (
        f"Turn 0 ('I'm coming to your house') should be 'Threat / Urgent Concern', got '{t0.classification}'"
    )
