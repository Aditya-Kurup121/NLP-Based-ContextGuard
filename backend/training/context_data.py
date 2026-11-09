"""Download and convert public context-labelled datasets into one JSONL format.

Run: .venv/Scripts/python -m backend.training.context_data

Each output row:
  {"source", "id", "group", "context": [{"speaker": "same"|"other", "text"}],
   "text", "label", "label_without_context" (CCC only, else null)}
"context" is oldest-first; "speaker" says whether the earlier turn's author is the
same as the target message's author. Splits are grouped (by conversation or post)
so no conversation appears in two splits.

Sources (raw files are not committed; check each source's terms before redistributing):
  CCC       - Xenos et al. 2021, github.com/ipavlopoulos/context_toxicity (Apache-2.0 repo)
  CONDA     - Weld et al. 2021, github.com/usydnlp/CONDA (no licence file; academic use with citation)
  DiaSafety - Sun et al. 2022, github.com/thu-coai/DiaSafety (Apache-2.0 repo)
"""
import ast
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "context"
OUT = ROOT / "data" / "processed" / "context"
MAX_CONTEXT_TURNS = 4
SEED = 42

FILES = {
    "CCC.csv": "https://raw.githubusercontent.com/ipavlopoulos/context_toxicity/master/data/CCC.csv",
    "CONDA_train.csv": "https://raw.githubusercontent.com/usydnlp/CONDA/main/data/CONDA_train.csv",
    "CONDA_valid.csv": "https://raw.githubusercontent.com/usydnlp/CONDA/main/data/CONDA_valid.csv",
    "DiaSafety_train.json": "https://raw.githubusercontent.com/thu-coai/DiaSafety/main/DiaSafety_dataset/train.json",
    "DiaSafety_val.json": "https://raw.githubusercontent.com/thu-coai/DiaSafety/main/DiaSafety_dataset/val.json",
    "DiaSafety_test.json": "https://raw.githubusercontent.com/thu-coai/DiaSafety/main/DiaSafety_dataset/test.json",
}
# DiaSafety categories about hostility toward people; medical/risk/bias-of-bot categories are out of scope.
DIASAFETY_CATEGORIES = {"Offending User", "Toxicity Agreement"}
# CONDA intent classes: E = explicit toxicity, I = implicit toxicity, A = action, O = other.
CONDA_TOXIC = {"E", "I"}


def download():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        path = RAW / name
        if not path.exists():
            with urlopen(url, timeout=120) as response:
                path.write_bytes(response.read())
        print(f"{name}: {path.stat().st_size} bytes, SHA256 {hashlib.sha256(path.read_bytes()).hexdigest()[:16]}…")


def majority(codes):
    values = ast.literal_eval(codes)
    return int(sum(values) / len(values) >= 0.5) if values else None


def load_ccc():
    rows = []
    for r in csv.DictReader(open(RAW / "CCC.csv", encoding="utf-8")):
        ic, oc = majority(r["tox_codes_ic"]), majority(r["tox_codes_oc"])
        if ic is None or oc is None or not r["text"].strip():
            continue
        context = [{"speaker": "other", "text": r["parent"].strip()}] if r["parent"].strip() else []
        rows.append({"source": "ccc", "id": f"ccc-{r['id']}", "group": f"ccc-{r['id']}", "context": context,
                     "text": r["text"].strip(), "label": ic, "label_without_context": oc})
    return rows


def load_conda(split):
    by_conv = defaultdict(list)
    for r in csv.DictReader(open(RAW / f"CONDA_{split}.csv", encoding="utf-8")):
        if r["utterance"].strip():
            by_conv[r["conversationId"]].append(r)
    rows = []
    for conv_id, turns in by_conv.items():
        turns.sort(key=lambda t: (int(t["chatTime"]), int(t["Id"])))
        for i, t in enumerate(turns):
            context = [
                {"speaker": "same" if p["playerSlot"] == t["playerSlot"] else "other", "text": p["utterance"].strip()}
                for p in turns[max(0, i - MAX_CONTEXT_TURNS):i]
            ]
            rows.append({"source": "conda", "id": f"conda-{t['Id']}", "group": f"conda-{split}-{conv_id}",
                         "context": context, "text": t["utterance"].strip(),
                         "label": int(t["intentClass"] in CONDA_TOXIC), "label_without_context": None})
    return rows


def load_diasafety(split):
    rows = []
    for i, r in enumerate(json.load(open(RAW / f"DiaSafety_{split}.json", encoding="utf-8"))):
        if r["category"] not in DIASAFETY_CATEGORIES or not r["response"].strip():
            continue
        rows.append({"source": "diasafety", "id": f"dia-{split}-{i}", "group": f"dia-{split}-{i}",
                     "context": [{"speaker": "other", "text": r["context"].strip()}],
                     "text": r["response"].strip(), "label": int(r["label"] == "Unsafe"),
                     "label_without_context": None})
    return rows


def group_split(rows, fractions, seed=SEED):
    """Split rows into len(fractions) parts by group, keeping each part's label mix similar."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["group"]].append(row)
    # Stratify groups by whether they contain any positive label.
    buckets = {0: [], 1: []}
    for key, members in groups.items():
        buckets[int(any(m["label"] for m in members))].append(key)
    rng = random.Random(seed)
    parts = [[] for _ in fractions]
    for keys in buckets.values():
        keys.sort()
        rng.shuffle(keys)
        start = 0
        for index, fraction in enumerate(fractions):
            end = len(keys) if index == len(fractions) - 1 else start + round(fraction * len(keys))
            for key in keys[start:end]:
                parts[index].extend(groups[key])
            start = end
    return parts


def build():
    download()
    ccc_train, ccc_val, ccc_test = group_split(load_ccc(), [0.6, 0.1, 0.3])
    conda_train, conda_val = group_split(load_conda("train"), [0.85, 0.15])
    conda_test = load_conda("valid")  # CONDA's own test split is unlabelled; its validation split is our test.
    splits = {
        "train": ccc_train + conda_train + load_diasafety("train"),
        "val": ccc_val + conda_val + load_diasafety("val"),
        "test": ccc_test + conda_test + load_diasafety("test"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, rows in splits.items():
        with open(OUT / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        summary[name] = {src: dict(Counter(r["label"] for r in rows if r["source"] == src)) for src in ("ccc", "conda", "diasafety")}
    groups = {name: {r["group"] for r in rows} for name, rows in splits.items()}
    assert not (groups["train"] & groups["test"]) and not (groups["train"] & groups["val"]) and not (groups["val"] & groups["test"])
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    build()
