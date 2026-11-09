"""Learned conversation-risk combiner.

Turns one engine analysis (rule classifications, rule signals, targeting pattern,
and the three model scores) into a fixed feature vector. A small classifier
trained on human-labelled conversations (backend/training/train_combiner.py)
maps those features to Low / Moderate / High / Critical.

The combiner is optional: without artifacts/combiner.joblib, nothing changes.
"""
from functools import lru_cache
from pathlib import Path

ARTIFACT = Path(__file__).resolve().parents[2] / "artifacts" / "combiner.joblib"
RISK_LEVELS = ["Low", "Moderate", "High", "Critical"]
CLASSIFICATIONS = [
    "Harmless / Neutral", "Friendly Banter", "Uncertain — More Context Needed",
    "Potentially Harmful", "Possible Cyberbullying", "Threat / Urgent Concern",
]
SIGNALS = [
    "has_insult_lexicon", "has_exclusion_phrase", "has_threat_lexicon", "is_sarcasm_suspect",
    "is_reciprocal_tease", "is_repeated_target", "is_victim_protest", "is_retaliatory_threat",
    "has_confrontation", "has_intimidation", "has_distress", "has_bystander_defense",
]
MODEL_SCORES = ["statistical_assessment", "transformer_assessment", "context_assessment"]


def _get(obj, name):
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)


def feature_names():
    names = [f"share:{c}" for c in CLASSIFICATIONS]
    names += [f"any:{s}" for s in SIGNALS] + [f"share:{s}" for s in SIGNALS]
    for m in MODEL_SCORES:
        names += [f"{m}:max", f"{m}:mean", f"{m}:share_toxic", f"{m}:available"]
    names += ["rules:risk_level", "rules:risk_score", "targeting:max_one_sided_turns",
              "targeting:asymmetric_pairs", "messages:log_count", "participants:count"]
    return names


def conversation_features(analysis):
    """analysis: AnalyzeResponse (or its dict). Returns a list of floats matching feature_names()."""
    import math
    messages = _get(analysis, "messages") or []
    n = max(1, len(messages))
    features = [sum(_get(m, "classification") == c for m in messages) / n for c in CLASSIFICATIONS]
    flags = [[bool(_get(_get(m, "signals"), s)) for s in SIGNALS] for m in messages] or [[False] * len(SIGNALS)]
    features += [float(any(col)) for col in zip(*flags)] + [sum(col) / n for col in zip(*flags)]
    for model in MODEL_SCORES:
        scored = [_get(m, model) for m in messages if _get(m, model)]
        values = [s["toxicity_score"] for s in scored]
        features += [max(values, default=0.0), sum(values) / len(values) if values else 0.0,
                     sum(s["label"] == "toxic" for s in scored) / n, float(bool(scored))]
    patterns = _get(analysis, "targeting_patterns") or []
    one_sided = [_get(p, "harmful_turns") for p in patterns if _get(p, "is_asymmetric")]
    risk = _get(analysis, "overall_risk")
    features += [
        float(RISK_LEVELS.index(risk)) if risk in RISK_LEVELS else 0.0,
        float(_get(analysis, "risk_score") or 0.0),
        float(max(one_sided, default=0)),
        float(len(one_sided)),
        math.log1p(len(messages)),
        float(len(_get(analysis, "participants") or [])),
    ]
    return features


@lru_cache(maxsize=1)
def combiner_model():
    if not ARTIFACT.exists():
        return None
    import joblib
    bundle = joblib.load(ARTIFACT)  # trusted, locally generated artifact only
    return bundle if bundle.get("feature_names") == feature_names() else None


def model_availability(analysis):
    """Which per-message model scores this analysis contains (the combiner's inputs depend on it)."""
    messages = _get(analysis, "messages") or []
    return {m: any(_get(msg, m) for msg in messages) for m in MODEL_SCORES}


def learned_risk(analysis):
    """Learned risk dict for this analysis, or None when no combiner is trained
    or the available models differ from those it was trained with (retrain it then)."""
    bundle = combiner_model()
    if bundle is None:
        return None
    if (_get(analysis, "messages") and bundle.get("model_availability")
            and model_availability(analysis) != bundle["model_availability"]):
        return None
    model = bundle["model"]
    probabilities = model.predict_proba([conversation_features(analysis)])[0]
    classes = list(model.classes_)
    best = classes[int(probabilities.argmax())]
    return {
        "risk": best,
        "probabilities": {c: round(float(p), 3) for c, p in zip(classes, probabilities)},
        "trained_on": bundle["trained_on"],
        "held_out_test": bundle.get("held_out_test"),
        "cross_validated": bundle["cross_validation"],
        "note": (
            "Learned from SYNTHETIC template conversations, a placeholder until real labelled chats exist; "
            "shown beside the rule-based risk, not instead of it."
            if "synthetic" in str(bundle["trained_on"].get("source", "")) else
            "Learned from human-labelled conversations; shown beside the rule-based risk, not instead of it."
        ),
    }
