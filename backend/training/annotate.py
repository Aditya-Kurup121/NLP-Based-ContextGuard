"""Terminal tool for labelling conversations. See annotation/GUIDELINES.md.

    python -m backend.training.annotate prepare                 # raw .txt files -> conversations.jsonl
    python -m backend.training.annotate label --annotator A     # label (resumable)
    python -m backend.training.annotate agreement               # Cohen's kappa A vs B
    python -m backend.training.annotate adjudicate              # resolve disagreements -> gold.jsonl
"""
import argparse
import json
import re
from pathlib import Path

from sklearn.metrics import cohen_kappa_score, confusion_matrix

from backend.app.services.parser import parse_conversation
from backend.app.services.whatsapp import parse_export

ROOT = Path(__file__).resolve().parents[2] / "annotation"
LABELS = ["Low", "Moderate", "High", "Critical"]
KEYS = {"1": "Low", "2": "Moderate", "3": "High", "4": "Critical"}


def read_jsonl(path):
    return [json.loads(line) for line in open(path, encoding="utf-8")] if path.exists() else []


def append_jsonl(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def messages_from_file(path):
    """WhatsApp exports via the importer; anything else as 'Name: message' lines."""
    text = path.read_text(encoding="utf-8-sig")
    try:
        parsed = parse_export(text, "DMY", anonymize=False)
        entries = [e for e in parsed["messages"] if e.get("kind") == "text" and e.get("text")]
        if entries:
            return [(e["speaker"], e["text"]) for e in entries]
    except (ValueError, KeyError, TypeError):
        pass
    return [(m.speaker, m.text) for m in parse_conversation(text)]


def anonymise(messages):
    """Replace speaker names (and mentions of them) with P1, P2, ... in order of appearance."""
    names = {}
    for speaker, _ in messages:
        names.setdefault(speaker, f"P{len(names) + 1}")
    out = []
    for speaker, text in messages:
        for real, alias in sorted(names.items(), key=lambda kv: -len(kv[0])):
            text = re.sub(rf"(?<!\w)@?{re.escape(real)}(?!\w)", alias, text, flags=re.IGNORECASE)
            first = real.split()[0]
            if len(first) > 2:
                text = re.sub(rf"(?<!\w)@?{re.escape(first)}(?!\w)", alias, text, flags=re.IGNORECASE)
        text = re.sub(r"\+?\d[\d\s-]{8,}\d", "[PHONE]", text)
        text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[EMAIL]", text)
        out.append({"speaker": names[speaker], "text": text})
    return out


def prepare(args):
    raw = ROOT / "raw"
    files = sorted(raw.glob("*.txt"))
    if not files:
        raise SystemExit(f"Put one conversation per .txt file in {raw} first.")
    existing = {row["id"] for row in read_jsonl(ROOT / "conversations.jsonl")}
    added = 0
    for path in files:
        conv_id = path.stem
        if conv_id in existing:
            continue
        messages = anonymise(messages_from_file(path))
        if len(messages) < 2:
            print(f"skipped {path.name}: fewer than 2 messages parsed")
            continue
        append_jsonl(ROOT / "conversations.jsonl", {"id": conv_id, "messages": messages})
        added += 1
    print(f"Added {added} conversations to {ROOT / 'conversations.jsonl'}. Check them for leftover personal details.")


def show(conv):
    print("\n" + "=" * 70 + f"\nConversation {conv['id']}\n" + "-" * 70)
    for i, m in enumerate(conv["messages"], 1):
        print(f"{i:>3}. {m['speaker']}: {m['text']}")
    print("-" * 70)


def ask_label():
    while True:
        key = input("Risk  [1] Low  [2] Moderate  [3] High  [4] Critical  [s] skip  [q] quit: ").strip().lower()
        if key in KEYS or key in ("s", "q"):
            return key


def label(args):
    conversations = read_jsonl(ROOT / "conversations.jsonl")
    out = ROOT / f"labels_{args.annotator}.jsonl"
    done = {row["id"] for row in read_jsonl(out)}
    todo = [c for c in conversations if c["id"] not in done]
    print(f"{len(done)} labelled, {len(todo)} to go. Labels save after each conversation.")
    for conv in todo:
        show(conv)
        key = ask_label()
        if key == "q":
            break
        if key == "s":
            continue
        targets = input("Message numbers that drive this label (e.g. 3,5; blank for none): ").strip()
        unsure = input("Unsure? [y/N]: ").strip().lower() == "y"
        append_jsonl(out, {"id": conv["id"], "label": KEYS[key], "unsure": unsure,
                           "target_messages": [int(x) for x in re.findall(r"\d+", targets)]})


def paired(a="A", b="B"):
    la = {r["id"]: r for r in read_jsonl(ROOT / f"labels_{a}.jsonl")}
    lb = {r["id"]: r for r in read_jsonl(ROOT / f"labels_{b}.jsonl")}
    ids = sorted(set(la) & set(lb))
    return ids, la, lb


def agreement(args):
    ids, la, lb = paired()
    if len(ids) < 2:
        raise SystemExit("Need at least 2 conversations labelled by both A and B.")
    ya = [LABELS.index(la[i]["label"]) for i in ids]
    yb = [LABELS.index(lb[i]["label"]) for i in ids]
    print(f"Conversations labelled by both: {len(ids)}")
    print(f"Raw agreement:                  {sum(x == y for x, y in zip(ya, yb)) / len(ids):.3f}")
    print(f"Cohen's kappa:                  {cohen_kappa_score(ya, yb, labels=range(4)):.3f}")
    print(f"Quadratic-weighted kappa:       {cohen_kappa_score(ya, yb, labels=range(4), weights='quadratic'):.3f}")
    print("Confusion (rows = A, columns = B):", LABELS)
    for name, row in zip(LABELS, confusion_matrix(ya, yb, labels=range(4))):
        print(f"  {name:9s} {row.tolist()}")
    disagreements = [i for i in ids if la[i]["label"] != lb[i]["label"]]
    print(f"Disagreements ({len(disagreements)}): {', '.join(disagreements[:40])}")


def adjudicate(args):
    ids, la, lb = paired()
    conversations = {c["id"]: c for c in read_jsonl(ROOT / "conversations.jsonl")}
    gold_path = ROOT / "gold.jsonl"
    done = {row["id"] for row in read_jsonl(gold_path)}
    for i in ids:
        if i in done:
            continue
        a, b = la[i], lb[i]
        if a["label"] == b["label"]:
            final = a["label"]
        else:
            show(conversations[i])
            print(f"A said {a['label']}, B said {b['label']}. Agree on one together.")
            key = ask_label()
            if key == "q":
                break
            if key == "s":
                continue
            final = KEYS[key]
        append_jsonl(gold_path, {"id": i, "label": final, "messages": conversations[i]["messages"],
                                 "annotator_labels": {"A": a["label"], "B": b["label"]},
                                 "target_messages": sorted(set(a["target_messages"]) | set(b["target_messages"]))})
    print(f"Gold labels: {len(read_jsonl(gold_path))} in {gold_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    p = sub.add_parser("label")
    p.add_argument("--annotator", required=True, choices=["A", "B"])
    sub.add_parser("agreement")
    sub.add_parser("adjudicate")
    args = parser.parse_args()
    {"prepare": prepare, "label": label, "agreement": agreement, "adjudicate": adjudicate}[args.command](args)
