"""How a message and its preceding turns become one transformer input.

Shared by training (backend/training/train_context.py) and serving
(backend/app/services/transformer.py) so both build inputs identically.

    context side:  [OTHER] earlier turn [SAME] earlier turn ...   (oldest first)
    target side:   the message being scored

Speaker tags say whether an earlier turn was written by the same person as the
target message; names are never given to the model. When the input is too long,
the oldest context is cut first and the target message is kept.
"""
SAME, OTHER, CTX = "[SAME]", "[OTHER]", "[CTX]"
SPECIAL_TOKENS = [SAME, OTHER, CTX]


def context_string(context, turns, speaker_tags=True):
    """context: list of {"speaker": "same"|"other", "text"} oldest-first."""
    recent = context[-turns:] if turns > 0 else []
    parts = []
    for turn in recent:
        tag = (SAME if turn["speaker"] == "same" else OTHER) if speaker_tags else CTX
        parts.append(f"{tag} {turn['text']}")
    return " ".join(parts)


def encode(tokenizer, examples, turns, speaker_tags, max_length):
    """Tokenize a batch. turns=0 means message-only (no context side)."""
    targets = [ex["text"] for ex in examples]
    if turns == 0:
        return tokenizer(targets, truncation=True, max_length=max_length, padding=True, return_tensors="pt")
    contexts = [context_string(ex["context"], turns, speaker_tags) for ex in examples]
    # Left-side truncation of the first sequence drops the oldest context first.
    previous_side = tokenizer.truncation_side
    tokenizer.truncation_side = "left"
    try:
        try:
            return tokenizer(contexts, targets, truncation="only_first", max_length=max_length,
                             padding=True, return_tensors="pt")
        except Exception:
            # A target longer than max_length on its own: trim whichever side is longer instead.
            return tokenizer(contexts, targets, truncation="longest_first", max_length=max_length,
                             padding=True, return_tensors="pt")
    finally:
        tokenizer.truncation_side = previous_side
