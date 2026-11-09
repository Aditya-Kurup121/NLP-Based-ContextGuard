"""Train the learned risk combiner on human-labelled conversations and compare it with the rules.

    python -m backend.training.train_combiner                       # uses annotation/gold.jsonl
    python -m backend.training.train_combiner --gold other.jsonl

Evaluation is repeated stratified cross-validation (the gold set is small), reporting
accuracy, macro-F1 and quadratic-weighted kappa for:
    rules_only  - the engine's existing overall_risk
    combiner    - logistic regression over rule features + model scores
After evaluation the combiner is refit on all gold data and saved to
backend/artifacts/combiner.joblib, with the cross-validated scores stored alongside.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.app.services.combiner import ARTIFACT, RISK_LEVELS, conversation_features, feature_names, model_availability
from backend.app.services.engine import ContextGuardAnalysisEngine
from backend.app.services.parser import ParsedMessage

ROOT = Path(__file__).resolve().parents[2]


def scores(truth, predicted):
    t = [RISK_LEVELS.index(x) for x in truth]
    p = [RISK_LEVELS.index(x) for x in predicted]
    return {
        "accuracy": float(accuracy_score(t, p)),
        "macro_f1": float(f1_score(t, p, average="macro", labels=sorted(set(t)), zero_division=0)),
        "quadratic_kappa": float(cohen_kappa_score(t, p, labels=range(4), weights="quadratic")),
    }


def make_model():
    return Pipeline([
        ("scale", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced")),
    ])


def analyse(gold):
    engine = ContextGuardAnalysisEngine()
    analyses = []
    for row in gold:
        messages = [ParsedMessage(i + 1, m["speaker"], m["text"], f"{m['speaker']}: {m['text']}")
                    for i, m in enumerate(row["messages"])]
        analyses.append(engine.analyze_messages(messages))
    return analyses


def train(gold_path, output, folds, repeats, seed=42, test_path=None):
    gold = [json.loads(line) for line in open(gold_path, encoding="utf-8")]
    labels = [row["label"] for row in gold]
    counts = Counter(labels)
    print(f"{len(gold)} gold conversations: {dict(counts)}")
    if min(counts.values()) < folds:
        folds = max(2, min(counts.values()))
        print(f"Smallest class is small; using {folds}-fold cross-validation.")

    analyses = analyse(gold)
    X = np.array([conversation_features(a) for a in analyses])
    y = np.array(labels)
    rules = np.array([a.overall_risk for a in analyses])

    cv = RepeatedStratifiedKFold(n_splits=folds, n_repeats=repeats, random_state=seed)
    fold_scores = {"rules_only": [], "combiner": []}
    for train_idx, test_idx in cv.split(X, y):
        model = make_model().fit(X[train_idx], y[train_idx])
        fold_scores["combiner"].append(scores(y[test_idx], model.predict(X[test_idx])))
        fold_scores["rules_only"].append(scores(y[test_idx], rules[test_idx]))
    summary = {
        name: {metric: {"mean": round(float(np.mean([f[metric] for f in runs])), 4),
                        "std": round(float(np.std([f[metric] for f in runs])), 4)}
               for metric in runs[0]}
        for name, runs in fold_scores.items()
    }
    print(json.dumps(summary, indent=2))

    final = make_model().fit(X, y)

    held_out = None
    if test_path:
        test = [json.loads(line) for line in open(test_path, encoding="utf-8")]
        test_analyses = analyse(test)
        test_y = [row["label"] for row in test]
        held_out = {
            "conversations": len(test), "source": str(test_path),
            "rules_only": scores(test_y, [a.overall_risk for a in test_analyses]),
            "combiner": scores(test_y, list(final.predict(np.array([conversation_features(a) for a in test_analyses])))),
        }
        if "scenario" in test[0]:
            by = {}
            for row, a, pred in zip(test, test_analyses, final.predict(np.array([conversation_features(t) for t in test_analyses]))):
                entry = by.setdefault(row["scenario"], {"n": 0, "rules_correct": 0, "combiner_correct": 0})
                entry["n"] += 1
                entry["rules_correct"] += int(a.overall_risk == row["label"])
                entry["combiner_correct"] += int(pred == row["label"])
            held_out["accuracy_by_scenario"] = {k: {"rules_only": round(v["rules_correct"] / v["n"], 3),
                                                    "combiner": round(v["combiner_correct"] / v["n"], 3), "n": v["n"]}
                                                for k, v in sorted(by.items())}
        print("Held-out test:", json.dumps(held_out, indent=2))
    coefficients = final.named_steps["classifier"].coef_
    top = {
        cls: sorted(zip(feature_names(), map(float, row)), key=lambda kv: -abs(kv[1]))[:8]
        for cls, row in zip(final.named_steps["classifier"].classes_, coefficients)
    }
    bundle = {
        "model": final, "feature_names": feature_names(),
        "trained_on": {"conversations": len(gold), "label_counts": dict(counts), "source": str(gold_path)},
        "cross_validation": {"folds": folds, "repeats": repeats, **summary},
        "held_out_test": held_out,
        "model_availability": model_availability(analyses[0]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, output)
    report = {**bundle["trained_on"], "cross_validation": bundle["cross_validation"], "held_out_test": held_out,
              "model_availability": bundle["model_availability"], "top_features": top}
    output.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {output}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, default=ROOT / "annotation" / "gold.jsonl")
    parser.add_argument("--output", type=Path, default=ARTIFACT)
    parser.add_argument("--test", type=Path, default=None, help="Optional held-out labelled conversations")
    parser.add_argument("--synthetic", action="store_true", help="Train on synthetic conversations, test on held-out-phrase ones")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()
    if args.synthetic:
        syn = ROOT / "backend" / "data" / "processed" / "synthetic"
        args.gold, args.test = syn / "conversations_train.jsonl", syn / "conversations_test.jsonl"
    train(args.gold, args.output, args.folds, args.repeats, test_path=args.test)
