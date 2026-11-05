"""
ContextGuard Regression Test - 13-Turn Conversation and Exclusion Scenario
===========================================================================
Root causes fixed before this test:
  1. PROTEST_PATTERNS: "why are you being so mean" missed (no 'being' variant).
  2. has_explicit_stop_request flag missing; retaliatory rule only checked grievances.
  3. BYSTANDER_DEFENSE_PATTERNS only matched pronouns; named target defence missed.
  4. EXCLUSION_PATTERNS: "just leave" fired on bystander defence phrasing.
  5. _classify_turn had no rule for has_bystander_defense / has_defender_challenge.
"""

import pytest
from backend.app.schemas.analysis import AnalyzeRequest, ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine
from backend.app.services.parser import parse_conversation
from backend.app.services.features import extract_all_features, infer_message_targets


@pytest.fixture(scope="module")
def engine():
    return ContextGuardAnalysisEngine()


def _msg(res, idx):
    return res.messages[idx]


CONV_13 = (
    "Jordan: You're such an idiot, you know that?\n"
    "Sam: What did I do now?\n"
    "Jordan: You always mess everything up. You're pathetic.\n"
    "Sam: That's not fair, please stop.\n"
    "Jordan: Loser. Nobody even likes you here.\n"
    "Sam: Why are you being so mean to me?\n"
    "Jordan: Because you're worthless. Stop wasting everyone's time.\n"
    "Sam: I'm asking you to stop. Please.\n"
    "Jordan: You'll regret asking me to stop.\n"
    "Sam: What does that mean?\n"
    "Alex: Jordan, come on, cut it out. This isn't necessary.\n"
    "Jordan: Mind your own business, Alex. Nobody asked you.\n"
    "Alex: Just leave Sam alone."
)

CTX_13 = ContextInfo(relationship="Classmates", setting="Group chat")


# ===========================================================================
# SECTION A - Feature extraction (Stage 1 intermediates)
# ===========================================================================

class TestFeatureExtraction:
    @pytest.fixture(scope="class")
    def features(self):
        parsed = parse_conversation(CONV_13)
        return list(zip(parsed, extract_all_features(parsed)))

    def test_t0_insult(self, features):
        _, feat = features[0]
        assert feat.has_insult, "T0: idiot must fire has_insult"

    def test_t2_insult(self, features):
        _, feat = features[2]
        assert feat.has_insult, "T2: pathetic must fire has_insult"

    def test_t3_protest(self, features):
        _, feat = features[3]
        assert feat.has_protest, "T3: please stop must fire has_protest"

    def test_t3_explicit_stop_request(self, features):
        _, feat = features[3]
        assert feat.has_explicit_stop_request, "T3: please stop must fire has_explicit_stop_request"

    def test_t4_insult(self, features):
        _, feat = features[4]
        assert feat.has_insult, "T4: loser must fire has_insult"

    def test_t5_protest_being_so_mean(self, features):
        _, feat = features[5]
        assert feat.has_protest, (
            "T5: 'Why are you being so mean' must fire has_protest "
            "(regression: 'being' variant was missing from PROTEST_PATTERNS)"
        )

    def test_t6_insult(self, features):
        _, feat = features[6]
        assert feat.has_insult, "T6: worthless must fire has_insult"

    def test_t7_explicit_stop_request(self, features):
        _, feat = features[7]
        assert feat.has_explicit_stop_request, (
            "T7: 'I'm asking you to stop' must fire has_explicit_stop_request"
        )

    def test_t8_retaliatory(self, features):
        _, feat = features[8]
        assert feat.has_retaliatory, "T8: 'You'll regret asking' must fire has_retaliatory"

    def test_t10_bystander_defence(self, features):
        _, feat = features[10]
        assert feat.has_bystander_defense, (
            "T10: 'cut it out' + 'this isn't necessary' must fire has_bystander_defense"
        )

    def test_t11_defender_challenge(self, features):
        _, feat = features[11]
        assert feat.has_defender_challenge, (
            "T11: 'Mind your own business' + 'Nobody asked you' must fire has_defender_challenge"
        )

    def test_t12_named_bystander_defence(self, features):
        _, feat = features[12]
        assert feat.has_bystander_defense, (
            "T12: 'Just leave Sam alone' must fire has_bystander_defense "
            "(regression: named target was not matched, only pronouns were)"
        )

    def test_t12_no_exclusion_false_positive(self, features):
        _, feat = features[12]
        assert not feat.has_exclusion, (
            "T12: 'Just leave Sam alone' must NOT fire has_exclusion "
            "(regression: bystander defence was falsely labelled as exclusion)"
        )

    def test_no_reciprocal_laughter(self):
        parsed = parse_conversation(CONV_13)
        feats = extract_all_features(parsed)
        e = ContextGuardAnalysisEngine()
        assert not e._check_reciprocal_laughter(feats, parsed), (
            "No laughter cues in this conversation; reciprocal-laughter must be False"
        )


# ===========================================================================
# SECTION B - Target inference (Stage 1 intermediates)
# ===========================================================================

class TestTargetInference:
    @pytest.fixture(scope="class")
    def targets(self):
        parsed = parse_conversation(CONV_13)
        return infer_message_targets(parsed)

    def test_t2_target_is_sam(self, targets):
        _, tgt = targets[2]
        assert tgt == "Sam", f"T2 Jordan should target Sam, got {tgt!r}"

    def test_t10_alex_targets_jordan(self, targets):
        _, tgt = targets[10]
        assert tgt == "Jordan", f"T10 Alex should target Jordan, got {tgt!r}"

    def test_t12_targets_sam_by_name(self, targets):
        _, tgt = targets[12]
        assert tgt == "Sam", f"T12 Alex should target Sam by name, got {tgt!r}"


# ===========================================================================
# SECTION C - Per-turn classification (Stage 2 intermediates)
# ===========================================================================

class TestPerTurnClassification:
    @pytest.fixture(scope="class")
    def result(self, engine):
        return engine.analyze(AnalyzeRequest(conversation=CONV_13, context=CTX_13))

    # Victim turns must NOT be Harmless/Neutral
    def test_t3_not_harmless(self, result):
        assert _msg(result, 3).classification != "Harmless / Neutral", (
            "T3 'please stop' must not be Harmless/Neutral"
        )

    def test_t5_not_harmless(self, result):
        assert _msg(result, 5).classification != "Harmless / Neutral", (
            "T5 'why are you being so mean' must not be Harmless/Neutral"
        )

    def test_t7_not_harmless(self, result):
        assert _msg(result, 7).classification != "Harmless / Neutral", (
            "T7 'I'm asking you to stop' must not be Harmless/Neutral"
        )

    # Aggressor turns must be escalated
    def test_t0_harmful(self, result):
        cls = _msg(result, 0).classification
        assert cls in ["Potentially Harmful", "Possible Cyberbullying"], f"T0 got {cls!r}"

    def test_t2_harmful(self, result):
        cls = _msg(result, 2).classification
        assert cls in ["Potentially Harmful", "Possible Cyberbullying"], f"T2 got {cls!r}"

    def test_t4_escalated(self, result):
        cls = _msg(result, 4).classification
        assert cls in ["Possible Cyberbullying", "Potentially Harmful"], f"T4 got {cls!r}"

    def test_t6_escalated(self, result):
        cls = _msg(result, 6).classification
        assert cls in ["Possible Cyberbullying", "Potentially Harmful"], f"T6 got {cls!r}"

    def test_t8_retaliatory_harmful(self, result):
        cls = _msg(result, 8).classification
        assert cls in ["Potentially Harmful", "Possible Cyberbullying", "Threat / Urgent Concern"], (
            f"T8 retaliatory warning must be harmful; got {cls!r}"
        )

    def test_t8_pattern_references_retaliation(self, result):
        m = _msg(result, 8)
        assert "Retaliatory" in m.detected_pattern or "Warning" in m.detected_pattern, (
            f"T8 pattern should reference retaliation; got {m.detected_pattern!r}"
        )

    def test_t8_evidence_references_stop_or_hostile(self, result):
        ev = " ".join(_msg(result, 8).contextual_evidence).lower()
        assert any(kw in ev for kw in ["stop", "request", "regret", "prior", "hostile", "warn"]), (
            f"T8 evidence should reference the stop request; got {_msg(result, 8).contextual_evidence}"
        )

    # Bystander turns
    def test_t10_bystander_harmless(self, result):
        assert _msg(result, 10).classification == "Harmless / Neutral", (
            f"T10 bystander defence should be Harmless/Neutral; got {_msg(result,10).classification!r}"
        )

    def test_t10_pattern_references_bystander(self, result):
        m = _msg(result, 10)
        assert "Bystander" in m.detected_pattern or "Defence" in m.detected_pattern, (
            f"T10 pattern should be Bystander Defence; got {m.detected_pattern!r}"
        )

    def test_t11_defender_challenge_harmful(self, result):
        cls = _msg(result, 11).classification
        assert cls in ["Potentially Harmful", "Possible Cyberbullying"], (
            f"T11 silencing bystander should be harmful; got {cls!r}"
        )

    def test_t12_not_cyberbullying(self, result):
        cls = _msg(result, 12).classification
        assert cls not in ["Possible Cyberbullying", "Threat / Urgent Concern"], (
            f"T12 'Just leave Sam alone' must NOT be labelled Cyberbullying; got {cls!r}"
        )

    def test_t12_harmless(self, result):
        assert _msg(result, 12).classification == "Harmless / Neutral", (
            f"T12 named bystander defence should be Harmless/Neutral; got {_msg(result,12).classification!r}"
        )


# ===========================================================================
# SECTION D - Targeting matrix (Stage 2 intermediates)
# ===========================================================================

class TestTargetingMatrix:
    @pytest.fixture(scope="class")
    def result(self, engine):
        return engine.analyze(AnalyzeRequest(conversation=CONV_13, context=CTX_13))

    def test_jordan_sam_is_asymmetric(self, result):
        js = [t for t in result.targeting_patterns if t.source == "Jordan" and t.target == "Sam"]
        assert js and js[0].is_asymmetric, "Jordan->Sam must be asymmetric"

    def test_jordan_sam_harmful_turns_gte_3(self, result):
        js = next(
            (t for t in result.targeting_patterns if t.source == "Jordan" and t.target == "Sam"),
            None
        )
        assert js and js.harmful_turns >= 3, (
            f"Jordan->Sam should have >=3 harmful turns; got {js.harmful_turns if js else 0}"
        )

    def test_sam_not_aggressor(self, result):
        sam_hostile = [
            t for t in result.targeting_patterns if t.source == "Sam" and t.harmful_turns > 0
        ]
        assert not sam_hostile, f"Sam should not appear as aggressor; got {sam_hostile}"


# ===========================================================================
# SECTION E - Aggregate risk and score (Stage 3)
# ===========================================================================

class TestAggregateRisk:
    @pytest.fixture(scope="class")
    def result(self, engine):
        return engine.analyze(AnalyzeRequest(conversation=CONV_13, context=CTX_13))

    def test_not_low(self, result):
        assert result.overall_risk != "Low", (
            f"13-turn insult conversation must NOT be LOW; got {result.overall_risk!r} score={result.risk_score}"
        )

    def test_is_high(self, result):
        assert result.overall_risk == "High", (
            f"Expected HIGH; got {result.overall_risk!r} score={result.risk_score}"
        )

    def test_score_above_50(self, result):
        assert result.risk_score > 50, f"Risk score should be >50; got {result.risk_score}"

    def test_harmful_count_positive(self, result):
        assert result.metrics.potentially_harmful_count > 0

    def test_neutral_not_dominant(self, result):
        neutral = result.metrics.neutral_count
        flagged = result.metrics.potentially_harmful_count + result.metrics.uncertain_count
        assert neutral < flagged, f"Neutral ({neutral}) should not dominate flagged ({flagged})"

    def test_summary_not_routine_neutral(self, result):
        s = result.conversation_summary.lower()
        bad_phrases = ["routine, neutral", "no concerning toxicity", "low risk"]
        assert not any(p in s for p in bad_phrases), (
            f"Summary should not describe hostile conversation as routine: {result.conversation_summary!r}"
        )


# ===========================================================================
# SECTION F - Previous exclusion scenario must still pass
# ===========================================================================

CONV_EXCL = (
    "Sam: Nobody wants you in this group.\n"
    "Sam: Seriously, just leave already.\n"
    "Sam: Everyone here would be happier without you."
)
CTX_EXCL = ContextInfo(relationship="Classmates", setting="Group chat")


def test_exclusion_still_high_risk(engine):
    res = engine.analyze(AnalyzeRequest(conversation=CONV_EXCL, context=CTX_EXCL))
    assert res.overall_risk == "High", f"Exclusion scenario must be HIGH; got {res.overall_risk!r}"


def test_exclusion_pattern_still_detected(engine):
    res = engine.analyze(AnalyzeRequest(conversation=CONV_EXCL, context=CTX_EXCL))
    assert any("Social Exclusion" in m.detected_pattern for m in res.messages)


def test_just_leave_already_still_fires(engine):
    res = engine.analyze(AnalyzeRequest(conversation=CONV_EXCL, context=CTX_EXCL))
    t1 = res.messages[1]
    assert t1.classification in ["Possible Cyberbullying", "Potentially Harmful"], (
        f"'just leave already' should still be harmful; got {t1.classification!r}"
    )


# ===========================================================================
# SECTION G - Bystander defence in benign conversation stays low risk
# ===========================================================================

def test_bystander_benign_stays_low(engine):
    req = AnalyzeRequest(
        conversation=(
            "Alice: Haha you owe me five bucks.\n"
            "Bob: Come on, cut it out, I'll pay you tomorrow lol.\n"
            "Alice: Okay okay fair enough."
        ),
        context=ContextInfo(relationship="Close friends", setting="Group chat")
    )
    res = engine.analyze(req)
    assert res.overall_risk == "Low", (
        f"Friendly conversation with 'cut it out' must stay LOW; got {res.overall_risk!r}"
    )
