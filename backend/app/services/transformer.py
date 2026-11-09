"""Fine-tuned DistilBERT toxicity scores, served alongside the classical model.

Two optional models:
  artifacts/transformer/    message-only toxicity model (Phase 2)
  artifacts/context_model/  context-aware model: reads each message with its previous turns

If torch/transformers are not installed or a model has not been trained, the
matching functions return None and the rest of the app works as before.
"""
import json
import logging
from functools import lru_cache
from pathlib import Path

from backend.app.services.context_format import encode

logger = logging.getLogger("ContextGuard")
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"
MODEL_DIR = ARTIFACTS / "transformer"
CONTEXT_MODEL_DIR = ARTIFACTS / "context_model"
BATCH_SIZE = 32


def _load(model_dir):
    if not (model_dir / "config.json").exists():
        return None
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        logger.info("Transformer model found but torch/transformers are not installed; skipping it.")
        return None
    config = json.loads((model_dir / "contextguard.json").read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device).eval()
    return model, tokenizer, config, device


@lru_cache(maxsize=1)
def transformer_model():
    """Message-only model as (model, tokenizer, config, device), or None."""
    return _load(MODEL_DIR)


@lru_cache(maxsize=1)
def context_model():
    """Context-aware model as (model, tokenizer, config, device), or None."""
    return _load(CONTEXT_MODEL_DIR)


def transformer_status():
    loaded = transformer_model()
    if loaded is None:
        return {"loaded": False}
    _, _, config, device = loaded
    return {"loaded": True, "base_model": config["base_model"], "threshold": config["threshold"], "device": device.type}


def context_model_status():
    loaded = context_model()
    if loaded is None:
        return {"loaded": False}
    _, _, config, device = loaded
    return {"loaded": True, "variant": config["variant"], "context_turns": config["turns"],
            "speaker_tags": config["speaker_tags"], "threshold": config["threshold"], "device": device.type}


def _probabilities(loaded, examples, turns, speaker_tags, max_length):
    import torch
    model, tokenizer, _, device = loaded
    out = []
    with torch.no_grad():
        for start in range(0, len(examples), BATCH_SIZE):
            batch = encode(tokenizer, examples[start:start + BATCH_SIZE], turns, speaker_tags, max_length).to(device)
            out.extend(torch.softmax(model(**batch).logits.float(), dim=-1)[:, 1].cpu().tolist())
    return out


def classify_texts_transformer(texts):
    """Message-only scores: one dict per text, or a list of None when the model is unavailable."""
    loaded = transformer_model()
    if loaded is None:
        return [None for _ in texts]
    if not texts:
        return []
    config = loaded[2]
    threshold = config["threshold"]
    probabilities = _probabilities(loaded, [{"text": t, "context": []} for t in texts], 0, False, config["max_length"])
    return [
        {
            "label": "toxic" if p >= threshold else "not toxic",
            "toxicity_score": round(float(p), 4),
            "threshold": threshold,
            "model": f"{config['base_model']} (fine-tuned)",
            "note": "Standalone comment model; reads one message at a time, so it does not see conversation context. Score is uncalibrated.",
        }
        for p in probabilities
    ]


def conversation_examples(speakers, texts, turns):
    """Build model inputs: each message with up to `turns` previous turns, tagged same/other speaker."""
    examples = []
    for i, (speaker, text) in enumerate(zip(speakers, texts)):
        context = [
            {"speaker": "same" if speakers[j] == speaker else "other", "text": texts[j]}
            for j in range(max(0, i - turns), i)
        ]
        examples.append({"text": text, "context": context})
    return examples


def classify_conversation_context(speakers, texts):
    """Context-aware scores for each message in order, or a list of None when the model is unavailable."""
    loaded = context_model()
    if loaded is None:
        return [None for _ in texts]
    if not texts:
        return []
    config = loaded[2]
    threshold, turns = config["threshold"], config["turns"]
    probabilities = _probabilities(loaded, conversation_examples(speakers, texts, turns), turns,
                                   config["speaker_tags"], config["max_length"])
    return [
        {
            "label": "toxic" if p >= threshold else "not toxic",
            "toxicity_score": round(float(p), 4),
            "threshold": threshold,
            "context_turns_used": min(i, turns),
            "model": f"{config['base_model']} context model ({config['variant']})",
            "note": f"Reads this message with up to {turns} previous turn(s), tagged by whether the same person wrote them. Score is uncalibrated.",
        }
        for i, p in enumerate(probabilities)
    ]
