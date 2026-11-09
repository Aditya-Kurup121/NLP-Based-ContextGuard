"""Train and compare message-only vs context-aware toxicity models.

Run after backend.training.context_data and backend.training.train_transformer:
    .venv/Scripts/python -m backend.training.train_context

Every variant starts from the Phase 2 fine-tuned DistilBERT and trains on the
same rows; only the input changes:
    message_only      the message alone
    context_tags      previous 3 turns with [SAME]/[OTHER] speaker tags
    context_no_tags   previous 3 turns, speaker tags replaced by [CTX]   (ablation)
    context_1turn     previous 1 turn with speaker tags                  (ablation)
plus "phase2_zero_shot": the Phase 2 model with no further training.

Epoch and threshold are chosen on validation macro-F1; test is scored once.
The context variant with the best validation macro-F1 is saved to
backend/artifacts/context_model/ for serving. Results: backend/artifacts/context_evaluation.json
"""
import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from backend.app.services.context_format import SPECIAL_TOKENS, encode
from backend.training.context_challenge import as_examples as challenge_examples, evaluate_challenge
from backend.training.context_data import group_split
from backend.training.train import ROOT, metrics
from backend.training.train_transformer import best_threshold, set_seed

DATA = ROOT / "data" / "processed" / "context"
SYNTHETIC = ROOT / "data" / "processed" / "synthetic"
BASE = ROOT / "artifacts" / "transformer"
VARIANTS = {
    "message_only": {"turns": 0, "speaker_tags": False, "counterfactual": False},
    "context_tags": {"turns": 3, "speaker_tags": True, "counterfactual": False},
    "context_no_tags": {"turns": 3, "speaker_tags": False, "counterfactual": False},
    "context_1turn": {"turns": 1, "speaker_tags": True, "counterfactual": False},
    "context_tags_cf": {"turns": 3, "speaker_tags": True, "counterfactual": True},
    "context_no_tags_cf": {"turns": 3, "speaker_tags": False, "counterfactual": True},
    # Also replay general comments from the Phase 2 training split, so fine-tuning on game/bot
    # data does not make the model forget that firm-but-civil pushback is not toxic.
    "message_only_mix": {"turns": 0, "speaker_tags": False, "counterfactual": False, "mix_comments": 20000},
    "context_tags_cf_mix": {"turns": 3, "speaker_tags": True, "counterfactual": True, "mix_comments": 20000},
    "context_no_tags_cf_mix": {"turns": 3, "speaker_tags": False, "counterfactual": True, "mix_comments": 20000},
}


def comment_rows(count, seed):
    """Sample standalone comments from the Phase 2 TRAINING split only (never its validation/test)."""
    from backend.training.train_transformer import load_splits
    (train_x, train_y), _, _ = load_splits(ROOT / "data" / "raw")
    rng = np.random.default_rng(seed)
    picks = rng.choice(len(train_x), size=min(count, len(train_x)), replace=False)
    return [{"source": "civil_comments", "id": f"cc-{i}", "group": f"cc-{i}", "context": [],
             "text": train_x[i], "label": int(train_y[i]), "label_without_context": None} for i in picks]
DEFAULT_VARIANTS = ["message_only", "context_tags", "context_no_tags", "context_tags_cf", "context_no_tags_cf"]
# Behaviour gate a context model must pass before it is served (on the hand-written challenge set).
MAX_FALSE_FLAG_RATE = 0.25
MIN_DETECTION_RATE = 0.75


def counterfactual_rows(rows, seed, safe_fraction=0.5, toxic_fraction=0.3):
    """Extra training rows that break the shortcut "toxic thread => toxic message".

    - a non-toxic message placed after an unrelated toxic turn written by someone else stays 0
    - a toxic message placed after unrelated calm turns stays 1
    Context is borrowed from a different conversation, so it cannot change the message's meaning.
    """
    rng = np.random.default_rng(seed)
    toxic = [r for r in rows if r["label"] == 1]
    calm = [r for r in rows if r["label"] == 0]
    extra = []
    for row in rows:
        if row["label"] == 0 and rng.random() < safe_fraction:
            donor = toxic[rng.integers(len(toxic))]
        elif row["label"] == 1 and rng.random() < toxic_fraction:
            donor = calm[rng.integers(len(calm))]
        else:
            continue
        if donor["group"] == row["group"]:
            continue
        context = (donor["context"] + [{"speaker": "other", "text": donor["text"]}])[-3:]
        extra.append({**row, "id": row["id"] + "-cf", "context": context, "counterfactual": True})
    return extra


def load(name):
    return [json.loads(line) for line in open(DATA / f"{name}.jsonl", encoding="utf-8")]


@torch.no_grad()
def predict(model, tokenizer, rows, cfg, device, batch_size, max_length):
    model.eval()
    out = []
    for start in range(0, len(rows), batch_size):
        batch = encode(tokenizer, rows[start:start + batch_size], cfg["turns"], cfg["speaker_tags"], max_length).to(device)
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
            logits = model(**batch).logits
        out.append(torch.softmax(logits.float(), dim=-1)[:, 1].cpu().numpy())
    return np.concatenate(out)


def evaluate(rows, probabilities, threshold):
    """Overall, per-source, and CCC context-flip results."""
    labels = np.array([r["label"] for r in rows])
    predictions = (probabilities >= threshold).astype(int)
    result = {"overall": metrics(labels, predictions), "by_source": {}}
    for source in ("ccc", "conda", "diasafety"):
        idx = [i for i, r in enumerate(rows) if r["source"] == source]
        if idx:
            result["by_source"][source] = metrics(labels[idx], predictions[idx])
    # CCC posts whose majority label changes when annotators see the parent post.
    flips = [i for i, r in enumerate(rows) if r["source"] == "ccc" and r["label"] != r["label_without_context"]]
    stable = [i for i, r in enumerate(rows) if r["source"] == "ccc" and r["label"] == r["label_without_context"]]
    result["ccc_context_flips"] = {
        "count": len(flips),
        "accuracy_vs_in_context_label": float((predictions[flips] == labels[flips]).mean()) if flips else None,
        "accuracy_on_non_flipped": float((predictions[stable] == labels[stable]).mean()) if stable else None,
    }
    return result


def summarise(name, result):
    o, f = result["test"]["overall"], result["test"]["ccc_context_flips"]
    by = result["test"]["by_source"]
    print(f"{name:18s} test macro-F1 {o['macro_f1']:.3f} | conda {by['conda']['macro_f1']:.3f} | "
          f"diasafety {by['diasafety']['macro_f1']:.3f} | ccc flips acc {f['accuracy_vs_in_context_label']:.3f} "
          f"(n={f['count']})", flush=True)


def train_variant(name, cfg, train_rows, val_rows, test_rows, args, device):
    set_seed(args.seed)
    if cfg.get("counterfactual"):
        extra = counterfactual_rows(train_rows, args.seed)
        print(f"[{name}] + {len(extra)} counterfactual rows", flush=True)
        train_rows = train_rows + extra
    if cfg.get("mix_comments"):
        extra = comment_rows(cfg["mix_comments"], args.seed)
        print(f"[{name}] + {len(extra)} general comments (Phase 2 training split, no context)", flush=True)
        train_rows = train_rows + extra
    tokenizer = AutoTokenizer.from_pretrained(BASE)
    tokenizer.add_special_tokens({"additional_special_tokens": SPECIAL_TOKENS})
    model = AutoModelForSequenceClassification.from_pretrained(BASE)
    model.resize_token_embeddings(len(tokenizer))
    model.to(device)

    labels = np.array([r["label"] for r in train_rows])
    weights = torch.tensor(len(labels) / (2 * np.bincount(labels, minlength=2)), dtype=torch.float, device=device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)
    steps_per_epoch = -(-len(train_rows) // args.batch_size)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.06 * steps_per_epoch * args.epochs), steps_per_epoch * args.epochs)
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    rng = np.random.default_rng(args.seed)

    history, best_state, best_val = [], None, -1.0
    started = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train()
        order = rng.permutation(len(train_rows))
        running = 0.0
        for step, start in enumerate(range(0, len(order), args.batch_size), 1):
            batch_rows = [train_rows[i] for i in order[start:start + args.batch_size]]
            batch = encode(tokenizer, batch_rows, cfg["turns"], cfg["speaker_tags"], args.max_length).to(device)
            target = torch.tensor([r["label"] for r in batch_rows], device=device)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(**batch).logits
            loss = loss_fn(logits.float(), target)
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            running += loss.item()
            if step % 500 == 0:
                print(f"[{name}] epoch {epoch} step {step}/{steps_per_epoch} loss {running / step:.4f}", flush=True)
        val_prob = predict(model, tokenizer, val_rows, cfg, device, args.batch_size * 2, args.max_length)
        val_f1 = metrics([r["label"] for r in val_rows], (val_prob >= 0.5).astype(int))["macro_f1"]
        history.append({"epoch": epoch, "train_loss": round(running / steps_per_epoch, 4), "validation_macro_f1_at_0.5": round(val_f1, 4)})
        print(f"[{name}] epoch {epoch} done: validation macro-F1 @0.5 = {val_f1:.4f}", flush=True)
        if val_f1 > best_val:
            best_val, best_state = val_f1, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    return model, tokenizer, history, round(time.time() - started)


def run(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}", flush=True)
    train_rows, val_rows, test_rows = load("train"), load("val"), load("test")
    if args.limit:  # smoke-test mode: small evenly spaced sample of each split
        train_rows, val_rows, test_rows = (rows[::max(1, len(rows) // args.limit)] for rows in (train_rows, val_rows, test_rows))
    print(f"rows: train {len(train_rows)}, val {len(val_rows)}, test {len(test_rows)}", flush=True)
    val_labels = [r["label"] for r in val_rows]
    report = {"data": json.loads((DATA / "summary.json").read_text(encoding="utf-8")),
              "settings": vars(args) | {"data_dir": str(DATA)}, "variants": {}}
    out_path = ROOT / "artifacts" / f"context_evaluation{args.output_suffix}.json"

    challenge_rows = challenge_examples()
    synthetic_test = []
    if args.synthetic:
        # Synthetic train conversations: 85% train, 15% validation (grouped by conversation).
        # The synthetic test file uses different phrases and is scored separately.
        syn_rows = [json.loads(line) for line in open(SYNTHETIC / "messages_train.jsonl", encoding="utf-8")]
        syn_train, syn_val = group_split(syn_rows, [0.85, 0.15], seed=args.seed)
        synthetic_test = [json.loads(line) for line in open(SYNTHETIC / "messages_test.jsonl", encoding="utf-8")]
        train_rows, val_rows = train_rows + syn_train, val_rows + syn_val
        val_labels = [r["label"] for r in val_rows]
        report["synthetic"] = {"train": len(syn_train), "validation": len(syn_val), "test": len(synthetic_test)}
        print(f"+ synthetic: train {len(syn_train)}, val {len(syn_val)}, held-out-phrase test {len(synthetic_test)}", flush=True)

    def record(name, cfg, model, tokenizer, extra):
        bs = args.batch_size * 2
        val_prob = predict(model, tokenizer, val_rows, cfg, device, bs, args.max_length)
        test_prob = predict(model, tokenizer, test_rows, cfg, device, bs, args.max_length)
        challenge_prob = predict(model, tokenizer, challenge_rows, cfg, device, bs, args.max_length)
        threshold = best_threshold(val_prob, val_labels)
        report["variants"][name] = {
            **cfg, **extra, "threshold": threshold,
            "validation": evaluate(val_rows, val_prob, threshold),
            "test": evaluate(test_rows, test_prob, threshold),
            "challenge": evaluate_challenge(challenge_prob, threshold),
        }
        if synthetic_test:
            syn_prob = predict(model, tokenizer, synthetic_test, cfg, device, bs, args.max_length)
            labels = np.array([r["label"] for r in synthetic_test])
            preds = (syn_prob >= threshold).astype(int)
            by_scenario = {}
            for row, ok in zip(synthetic_test, preds == labels):
                by_scenario.setdefault(row["scenario"], []).append(bool(ok))
            report["variants"][name]["synthetic_test"] = {
                **metrics(labels, preds),
                "accuracy_by_scenario": {k: round(sum(v) / len(v), 3) for k, v in by_scenario.items()},
            }
            st = report["variants"][name]["synthetic_test"]
            print(f"{'':18s} synthetic held-out macro-F1 {st['macro_f1']:.3f} | by scenario {st['accuracy_by_scenario']}", flush=True)
        summarise(name, report["variants"][name])
        c = report["variants"][name]["challenge"]
        print(f"{'':18s} challenge acc {c['accuracy']:.3f} | false flags on safe replies "
              f"{c['false_flag_rate_on_safe_replies']:.3f} | detection {c['detection_rate_on_harmful']:.3f} "
              f"| {c['by_category']}", flush=True)
        out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # Reference: Phase 2 model applied as-is, no training on these datasets.
    base_cfg = {"turns": 0, "speaker_tags": False}
    tokenizer = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForSequenceClassification.from_pretrained(BASE).to(device)
    record("phase2_zero_shot", {**base_cfg, "counterfactual": False}, model, tokenizer, {"trained_on_context_data": False})
    del model

    candidates = ROOT / "artifacts" / f"context_candidates{args.output_suffix}"
    for name in args.variants:
        cfg = VARIANTS[name]
        model, tokenizer, history, seconds = train_variant(name, cfg, train_rows, val_rows, test_rows, args, device)
        record(name, cfg, model, tokenizer, {"trained_on_context_data": True, "history": history, "training_seconds": seconds})
        if cfg["turns"] > 0:
            model.save_pretrained(candidates / name)
            tokenizer.save_pretrained(candidates / name)
        del model
        torch.cuda.empty_cache()

    # Serve the best-on-validation context variant that also passes the behaviour gate.
    passing = [
        name for name in args.variants
        if VARIANTS[name]["turns"] > 0
        and report["variants"][name]["challenge"]["false_flag_rate_on_safe_replies"] <= MAX_FALSE_FLAG_RATE
        and report["variants"][name]["challenge"]["detection_rate_on_harmful"] >= MIN_DETECTION_RATE
    ]
    served = max(passing, key=lambda n: report["variants"][n]["validation"]["overall"]["macro_f1"]) if passing else None
    save_dir = ROOT / "artifacts" / f"context_model{args.output_suffix}"
    shutil.rmtree(save_dir, ignore_errors=True)
    if served:
        shutil.copytree(candidates / served, save_dir)
        (save_dir / "contextguard.json").write_text(json.dumps({
            "variant": served, **VARIANTS[served], "threshold": report["variants"][served]["threshold"],
            "max_length": args.max_length, "base_model": "distilbert-base-uncased",
            "trained_from": "Phase 2 toxicity model, then CCC + CONDA + DiaSafety (context)",
            "challenge": report["variants"][served]["challenge"],
        }, indent=2), encoding="utf-8")
    shutil.rmtree(candidates, ignore_errors=True)
    report["served_context_variant"] = served
    report["selection_rule"] = (
        "Thresholds tuned on validation; test scored once per variant. Served = context variant with the highest "
        f"validation macro-F1 among those passing the behaviour gate (challenge false-flag rate <= {MAX_FALSE_FLAG_RATE}, "
        f"detection >= {MIN_DETECTION_RATE}). Because the challenge set gates serving, its numbers are not an unbiased test."
    )
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Served context variant: {served or 'none (no variant passed the behaviour gate)'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", nargs="+", default=DEFAULT_VARIANTS, choices=list(VARIANTS))
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--synthetic", action="store_true", help="Add synthetic conversations (backend.training.synthetic_conversations)")
    parser.add_argument("--limit", type=int, default=0, help="Smoke test on ~N rows per split")
    parser.add_argument("--output-suffix", default="", help="Write context_evaluation<suffix>.json / context_model<suffix>")
    run(parser.parse_args())
