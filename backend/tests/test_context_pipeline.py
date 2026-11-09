import json

import pytest

from backend.app.services import combiner, transformer
from backend.app.services.context_format import context_string
from backend.training import annotate
from backend.training.context_data import group_split
from backend.training.evaluator_data import BENCHMARK_AS_GOLD
from backend.training.train_combiner import train as train_combiner


def test_context_string_tags_and_order():
    ctx = [{"speaker": "other", "text": "a"}, {"speaker": "same", "text": "b"}, {"speaker": "other", "text": "c"}]
    assert context_string(ctx, 2) == "[SAME] b [OTHER] c"          # most recent turns, oldest first
    assert context_string(ctx, 2, speaker_tags=False) == "[CTX] b [CTX] c"
    assert context_string(ctx, 0) == ""


def test_conversation_examples_mark_same_and_other_speaker():
    examples = transformer.conversation_examples(["A", "B", "A"], ["hi", "you idiot", "rude"], turns=3)
    assert examples[0]["context"] == []
    assert examples[2]["context"] == [{"speaker": "same", "text": "hi"}, {"speaker": "other", "text": "you idiot"}]


def test_group_split_never_shares_a_group():
    rows = [{"group": f"g{i // 3}", "label": int(i % 7 == 0)} for i in range(300)]
    parts = group_split(rows, [0.6, 0.2, 0.2])
    groups = [{r["group"] for r in part} for part in parts]
    assert sum(len(p) for p in parts) == 300
    assert not (groups[0] & groups[1]) and not (groups[0] & groups[2]) and not (groups[1] & groups[2])


def test_context_model_absent_degrades_gracefully(monkeypatch, tmp_path):
    monkeypatch.setattr(transformer, "CONTEXT_MODEL_DIR", tmp_path / "absent")
    transformer.context_model.cache_clear()
    try:
        assert transformer.classify_conversation_context(["A", "B"], ["hi", "hey"]) == [None, None]
        assert transformer.context_model_status() == {"loaded": False}
    finally:
        transformer.context_model.cache_clear()


def test_anonymise_replaces_names_mentions_and_contacts():
    out = annotate.anonymise([("Rahul Sharma", "hi @Priya call 98765 43210"), ("Priya", "Rahul stop, mail me a@b.com")])
    assert [m["speaker"] for m in out] == ["P1", "P2"]
    assert "Priya" not in out[0]["text"] and "[PHONE]" in out[0]["text"]
    assert "Rahul" not in out[1]["text"] and "[EMAIL]" in out[1]["text"]


def test_combiner_trains_saves_and_serves(tmp_path, monkeypatch):
    gold = tmp_path / "gold.jsonl"
    gold.write_text("\n".join(json.dumps(row) for row in BENCHMARK_AS_GOLD), encoding="utf-8")
    out = tmp_path / "combiner.joblib"
    report = train_combiner(gold, out, folds=2, repeats=2)
    assert {"rules_only", "combiner"} <= set(report["cross_validation"])
    assert out.exists() and out.with_suffix(".json").exists()

    monkeypatch.setattr(combiner, "ARTIFACT", out)
    combiner.combiner_model.cache_clear()
    try:
        from fastapi.testclient import TestClient
        from backend.app.main import app
        res = TestClient(app).post("/api/analyze", json={"conversation": "A: nobody wants you here\nA: just leave"})
        learned = res.json()["learned_risk"]
        assert learned["risk"] in combiner.RISK_LEVELS
        assert abs(sum(learned["probabilities"].values()) - 1) < 0.01
    finally:
        combiner.combiner_model.cache_clear()


def test_feature_vector_matches_names():
    from backend.app.services.engine import ContextGuardAnalysisEngine
    from backend.app.schemas.analysis import AnalyzeRequest
    analysis = ContextGuardAnalysisEngine().analyze(AnalyzeRequest(conversation="A: hi\nB: you idiot\nA: please stop"))
    assert len(combiner.conversation_features(analysis)) == len(combiner.feature_names())


def test_counterfactual_rows_keep_labels_and_borrow_other_context():
    from backend.training.train_context import counterfactual_rows
    rows = [{"id": f"r{i}", "group": f"g{i}", "label": int(i % 4 == 0), "text": f"t{i}",
             "context": [{"speaker": "same", "text": f"own{i}"}]} for i in range(200)]
    extra = counterfactual_rows(rows, seed=1)
    assert extra, "expected some counterfactual rows"
    originals = {r["id"]: r for r in rows}
    for row in extra:
        source = originals[row["id"][:-3]]
        assert row["label"] == source["label"] and row["text"] == source["text"]
        assert all(turn["text"] != f"own{row['id'][1:-3]}" for turn in row["context"])  # context comes from elsewhere
        assert row["context"][-1]["speaker"] == "other"


def test_challenge_scoring_counts_false_flags():
    from backend.training.context_challenge import CHALLENGE, evaluate_challenge
    flag_everything = evaluate_challenge([1.0] * len(CHALLENGE), threshold=0.5)
    assert flag_everything["false_flag_rate_on_safe_replies"] == 1.0
    assert flag_everything["detection_rate_on_harmful"] == 1.0
    perfect = evaluate_challenge([float(c["label"]) for c in CHALLENGE], threshold=0.5)
    assert perfect["accuracy"] == 1.0 and perfect["false_flag_rate_on_safe_replies"] == 0.0


@pytest.mark.skipif(transformer.context_model() is None, reason="No context model served")
def test_served_context_model_passed_behaviour_gate():
    from backend.training.train_context import MAX_FALSE_FLAG_RATE, MIN_DETECTION_RATE
    challenge = transformer.context_model()[2]["challenge"]
    assert challenge["false_flag_rate_on_safe_replies"] <= MAX_FALSE_FLAG_RATE
    assert challenge["detection_rate_on_harmful"] >= MIN_DETECTION_RATE


def test_synthetic_data_has_no_challenge_leakage_and_split_phrases():
    from backend.training.synthetic_conversations import check_leakage, split_pools
    assert check_leakage()["passes"]
    train, test = split_pools()
    for pool in train:
        assert not set(train[pool]) & set(test[pool]), pool


def test_combiner_refuses_when_available_models_change(monkeypatch):
    bundle = {"model": None, "feature_names": combiner.feature_names(), "trained_on": {},
              "cross_validation": {}, "model_availability": {m: False for m in combiner.MODEL_SCORES}}
    monkeypatch.setattr(combiner, "combiner_model", lambda: bundle)
    analysis = {"messages": [{"transformer_assessment": {"toxicity_score": 0.9, "label": "toxic"}}]}
    assert combiner.learned_risk(analysis) is None
