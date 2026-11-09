"""Fine-tune DistilBERT for standalone comment toxicity on the same splits as train.py.

Run after backend.training.train (it adds results to the same evaluation.json):
    .venv/Scripts/python -m backend.training.train_transformer

Uses the exact train/validation/test split of the classical models (same dedup,
same seed, same stratification), so the comparison table is like-for-like.
The decision threshold is chosen on validation only; test is scored once at the end.
Needs: pip install -r backend/requirements-transformer.txt (GPU strongly recommended).
"""
import argparse
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from backend.training.train import ROOT, metrics, read_unique

BASE_MODEL = "distilbert-base-uncased"
MODEL_KEY = "distilbert_finetuned"


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_splits(data_dir):
    # Mirrors train.train() exactly so every model sees identical data.
    train_rows = read_unique(data_dir / "train.jsonl")
    test_rows = read_unique(data_dir / "test.jsonl")
    overlap = set(train_rows) & set(test_rows)
    test_rows = {key: row for key, row in test_rows.items() if key not in overlap}
    text, labels = zip(*train_rows.values())
    train_x, val_x, train_y, val_y = train_test_split(
        list(text), list(labels), test_size=0.2, random_state=42, stratify=labels,
    )
    test_x, test_y = zip(*test_rows.values())
    return (train_x, train_y), (val_x, val_y), (list(test_x), list(test_y))


def batches(tokenizer, texts, labels, batch_size, max_length, shuffle):
    order = list(range(len(texts)))

    def collate(indices):
        encoded = tokenizer([texts[i] for i in indices], truncation=True, max_length=max_length,
                            padding=True, return_tensors="pt")
        if labels is not None:
            encoded["labels"] = torch.tensor([labels[i] for i in indices])
        return encoded

    return DataLoader(order, batch_size=batch_size, shuffle=shuffle, collate_fn=collate)


@torch.no_grad()
def toxic_probabilities(model, tokenizer, texts, device, batch_size, max_length):
    model.eval()
    out = []
    for batch in batches(tokenizer, texts, None, batch_size, max_length, shuffle=False):
        batch = {k: v.to(device) for k, v in batch.items()}
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
            logits = model(**batch).logits
        out.append(torch.softmax(logits.float(), dim=-1)[:, 1].cpu().numpy())
    return np.concatenate(out)


def best_threshold(probabilities, labels):
    """Pick the threshold with the highest validation macro-F1 (grid 0.05..0.95)."""
    # Exact two-decimal grid, so the saved threshold behaves identically at serving time.
    best = (0.5, -1.0)
    for hundredths in range(5, 96):
        threshold = hundredths / 100
        score = metrics(labels, (probabilities >= threshold).astype(int))["macro_f1"]
        if score > best[1]:
            best = (threshold, score)
    return best[0]


def train(data_dir, output_dir, epochs, batch_size, max_length, lr, seed):
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})", flush=True)

    (train_x, train_y), (val_x, val_y), (test_x, test_y) = load_splits(data_dir)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=2).to(device)

    # Class-weighted loss: toxic comments are ~8% of the data.
    counts = np.bincount(train_y, minlength=2)
    class_weights = torch.tensor(len(train_y) / (2 * counts), dtype=torch.float, device=device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)

    loader = batches(tokenizer, train_x, train_y, batch_size, max_length, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = epochs * len(loader)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.06 * total_steps), total_steps)
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")

    started = time.time()
    history = []
    best_state, best_val = None, -1.0
    for epoch in range(1, epochs + 1):
        model.train()
        running = 0.0
        for step, batch in enumerate(loader, 1):
            batch = {k: v.to(device) for k, v in batch.items()}
            labels = batch.pop("labels")
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(**batch).logits
            loss = loss_fn(logits.float(), labels)
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            running += loss.item()
            if step % 250 == 0:
                print(f"epoch {epoch} step {step}/{len(loader)} loss {running / step:.4f}", flush=True)
        val_prob = toxic_probabilities(model, tokenizer, val_x, device, batch_size * 2, max_length)
        val_f1 = metrics(val_y, (val_prob >= 0.5).astype(int))["macro_f1"]
        history.append({"epoch": epoch, "train_loss": round(running / len(loader), 4), "validation_macro_f1_at_0.5": round(val_f1, 4)})
        print(f"epoch {epoch} done: validation macro-F1 @0.5 = {val_f1:.4f}", flush=True)
        if val_f1 > best_val:
            best_val = val_f1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    # Keep the epoch with the best validation score, then tune the threshold on validation.
    model.load_state_dict(best_state)
    val_prob = toxic_probabilities(model, tokenizer, val_x, device, batch_size * 2, max_length)
    threshold = best_threshold(val_prob, val_y)
    print(f"Validation-selected threshold: {threshold}", flush=True)

    # Test is touched exactly once, after all choices are locked.
    test_prob = toxic_probabilities(model, tokenizer, test_x, device, batch_size * 2, max_length)
    result = {
        "validation": metrics(val_y, (val_prob >= threshold).astype(int)),
        "test": metrics(test_y, (test_prob >= threshold).astype(int)),
        "test_at_0.5": metrics(test_y, (test_prob >= 0.5).astype(int)),
    }

    model_dir = output_dir / "transformer"
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)
    config = {
        "base_model": BASE_MODEL,
        "threshold": threshold,
        "max_length": max_length,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "seed": seed,
        "history": history,
        "training_seconds": round(time.time() - started),
        "device": torch.cuda.get_device_name(0) if device.type == "cuda" else "CPU",
        "torch_version": torch.__version__,
    }
    (model_dir / "contextguard.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    # Merge into the shared report so the Language lab table compares all models.
    report_path = output_dir / "evaluation.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["models"][MODEL_KEY] = result
    report["transformer"] = {**config, "selection_note": "Epoch and threshold chosen on validation macro-F1; test scored once afterwards."}
    report["selected_model"] = max(report["models"], key=lambda name: report["models"][name]["validation"]["macro_f1"])
    report["selection_rule"] = "Highest validation macro-F1 across all models; test never used for selection"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    test = result["test"]
    print(json.dumps({
        "threshold": threshold,
        "test_macro_f1": round(test["macro_f1"], 4),
        "test_toxic_precision": round(test["per_class"]["toxic"]["precision"], 4),
        "test_toxic_recall": round(test["per_class"]["toxic"]["recall"], 4),
        "selected_model": report["selected_model"],
        "minutes": round((time.time() - started) / 60, 1),
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    train(args.data_dir, args.output_dir, args.epochs, args.batch_size, args.max_length, args.lr, args.seed)
