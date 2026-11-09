"""Train on public comment labels. Never use conversation demo risk labels.

Run: .venv/Scripts/python -m backend.training.train
Only trusted, locally generated joblib artifacts should be loaded by the server.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import joblib
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from backend.training.manual_nb import ManualMultinomialNB

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(text):
    canonical = re.sub(r"\s+", " ", text.casefold()).strip()
    return hashlib.sha256(canonical.encode()).hexdigest()


def read_unique(path):
    # Remove conflicting duplicate labels, rather than arbitrarily trusting one.
    unique, conflicts = {}, set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        row = json.loads(line)
        text, label = row["text"].strip(), int(row["label"])
        if not text or label not in (0, 1):
            continue
        key = fingerprint(text)
        if key in unique and unique[key][1] != label:
            conflicts.add(key)
        unique[key] = (text, label)
    return {key: value for key, value in unique.items() if key not in conflicts}


def metrics(y, predictions):
    return {
        "accuracy": float(accuracy_score(y, predictions)),
        "macro_f1": float(f1_score(y, predictions, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y, predictions, labels=[0, 1]).tolist(),
        "per_class": classification_report(
            y, predictions, labels=[0, 1], target_names=["not toxic", "toxic"],
            output_dict=True, zero_division=0,
        ),
    }


def train(data_dir=ROOT / "data" / "raw", output_dir=ROOT / "artifacts"):
    train_rows = read_unique(data_dir / "train.jsonl")
    test_rows = read_unique(data_dir / "test.jsonl")
    overlap = set(train_rows) & set(test_rows)
    test_rows = {key: row for key, row in test_rows.items() if key not in overlap}
    text, labels = zip(*train_rows.values())
    train_x, val_x, train_y, val_y = train_test_split(
        list(text), list(labels), test_size=0.2, random_state=42, stratify=labels,
    )
    if not test_rows:
        raise ValueError("No independent test samples remain after duplicate removal.")
    test_x, test_y = zip(*test_rows.values())
    models = {
        "bow_naive_bayes_from_scratch": Pipeline([
            ("vectorizer", CountVectorizer(ngram_range=(1, 1), max_features=30000)),
            ("classifier", ManualMultinomialNB(alpha=1.0)),
        ]),
        "bow_naive_bayes": Pipeline([
            ("vectorizer", CountVectorizer(ngram_range=(1, 1), max_features=30000)),
            ("classifier", MultinomialNB(alpha=1.0)),
        ]),
        "tfidf_logistic_regression": Pipeline([
            ("vectorizer", TfidfVectorizer(ngram_range=(1, 2), max_features=30000, sublinear_tf=True)),
            ("classifier", LogisticRegression(max_iter=600, class_weight="balanced", random_state=42)),
        ]),
    }
    results = {}
    for name, model in models.items():
        model.fit(train_x, train_y)
        results[name] = {"validation": metrics(val_y, model.predict(val_x))}
        print(f"{name}: validation macro-F1={results[name]['validation']['macro_f1']:.4f}", flush=True)
    selected = max(results, key=lambda name: results[name]["validation"]["macro_f1"])
    # Lock selection before accessing test labels. Do not refit on the held-out data.
    for name, model in models.items():
        results[name]["test"] = metrics(test_y, model.predict(test_x))
    majority = DummyClassifier(strategy="most_frequent").fit([[0]] * len(train_y), train_y)
    majority_result = metrics(test_y, majority.predict([[0]] * len(test_y)))
    revision_file = data_dir / "revision.txt"
    report = {
        "dataset": "SetFit/toxic_conversations_50k",
        "source_url": "https://huggingface.co/datasets/SetFit/toxic_conversations_50k",
        "dataset_revision": revision_file.read_text(encoding="utf-8-sig").strip() if revision_file.exists() else "user-supplied",
        "task": "Binary toxicity classification of standalone English comments, NOT conversation risk prediction",
        "seed": 42,
        "scikit_learn_version": sklearn.__version__,
        "source_file_sha256": {name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest() for name in ("train.jsonl", "test.jsonl")},
        "split_sizes": {"train": len(train_x), "validation": len(val_x), "test": len(test_x)},
        "class_counts": {"train": dict(Counter(train_y)), "validation": dict(Counter(val_y)), "test": dict(Counter(test_y))},
        "exact_cross_split_duplicates_removed": len(overlap),
        "selection_rule": "Highest validation macro-F1; fixed decision threshold 0.5; test never used for selection",
        "selected_model": selected,
        "models": results,
        "majority_baseline": majority_result,
        "limitations": [
            "Comment labels are not conversation-level cyberbullying or intent labels.",
            "Exact normalized duplicates are removed; near duplicates and source-thread overlap cannot be ruled out.",
            "The source does not supply conversation/thread identifiers in these files.",
            "No claim of probability calibration, fairness, or Hindi/Hinglish performance.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        joblib.dump(model, output_dir / f"{name}.joblib")
    joblib.dump(models[selected], output_dir / "toxicity.joblib")
    (output_dir / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"selected_model": selected, "test": results[selected]["test"], "split_sizes": report["split_sizes"]}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    train(args.data_dir, args.output_dir)
