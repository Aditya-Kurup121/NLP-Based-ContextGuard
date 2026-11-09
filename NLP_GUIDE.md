# ContextGuard: NLP experiments and reproducibility

## Run the project

From this project directory, run `./Start-ContextGuard.ps1`. It starts the backend and frontend in hidden processes, checks both HTTP endpoints, and prints the preview URL. Add `-OpenBrowser` to open your default browser. It needs Node.js on PATH and `npm install` already run in `frontend`.

The working Python environment is `.venv`, not the old `venv` copied from a different Windows account. Backend dependencies are in `backend/requirements.txt`. After changing backend sources or model artifacts, restart the project's backend. The frontend supports hot reload.

## Rebuild the NLP assets

```powershell
python -m venv .venv
uv pip install --python .venv/Scripts/python.exe -r backend/requirements.txt
uv pip install --python .venv/Scripts/python.exe https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
./.venv/Scripts/python.exe -m backend.training.download_data
./.venv/Scripts/python.exe -m backend.training.train
./.venv/Scripts/python.exe -m backend.training.tokenization
./.venv/Scripts/python.exe -m pytest backend/tests -q
```

The classical models run on CPU. The optional DistilBERT fine-tune (below) needs PyTorch and is practical on a GPU: about 15 minutes on an RTX 3050 Laptop GPU (4 GB). Without it the app works as before and simply omits the transformer score.

## What is implemented

| Outcome | Demonstrable work |
|---|---|
| CO1 | Noise removal (HTML, zero-width chars), normalization preserving negation/emojis, multi-level tokenization (sentence, word, character, WordPiece, BPE), stopword removal with explicit negation preservation, Porter & Lancaster stemming vs spaCy lemmatization, vocabulary counts |
| CO2 | Handcrafted conversation features, unigram/bigram/trigram inspection, Levenshtein edit distance with DP matrix and backtrace operations, manual BoW and smoothed TF-IDF matrix, Skip-gram Word2Vec embeddings (NumPy SGNS) with cosine similarity, nearest neighbors, analogies, and custom corpus retraining |
| CO3 | spaCy English model (`en_core_web_sm`) provides POS tags, dependency parse trees, noun chunks, and named entities with character spans; from-scratch First-Order Hidden Markov Model (HMM) POS tagger with Laplace smoothing and Viterbi dynamic programming decoding; side-by-side POS comparison |
| CO4 | From-scratch Multinomial Naive Bayes, scikit-learn Naive Bayes, TF-IDF Logistic Regression; validation-selected model; held-out test evaluation metrics (accuracy, precision, recall, macro-F1, confusion matrix) and majority baseline; multi-turn contextual cyberbullying detection engine |
| CO5 | Optional hosted LLM second-opinion endpoint (Hugging Face chat completion), explicit consent gate, bounded/validated structured output schema, exact-quote evidence verification, and complete graceful degradation when unconfigured |

Conversation risk remains a contextual rule assessment. Standalone toxicity is an independent statistical signal. Do not describe these as a trained conversation-level classifier or claim that the hybrid improves context accuracy without a labeled conversation experiment.

## Dataset and split policy

Source: [SetFit/toxic_conversations_50k](https://huggingface.co/datasets/SetFit/toxic_conversations_50k), derived from Jigsaw/Civil Comments. The source card describes binary toxicity labels and substantial class imbalance. These are individual comments, not multi-turn conversations. Downloaded raw data is ignored by Git; check the original source terms before redistributing or deploying commercially.

The downloader records a repository revision. Training records file SHA256 hashes, seed, package version, split sizes, class supports and limitations in `backend/artifacts/evaluation.json`.

- Drop blank rows and within-split conflicting exact duplicates.
- Canonicalize case and whitespace for duplicate identification.
- Remove source-test comments that duplicate source-training comments.
- Split deduplicated source training into 80% train and 20% validation, stratified with seed 42.
- Fit vocabulary and classifiers only on the training partition.
- Select the model by validation macro-F1, with threshold fixed at 0.5.
- Report the held-out source test once after model selection. It is not used to select the model.
- Subword vocabularies are also trained only on the training partition; they demonstrate segmentation and are not pretrained transformer tokenizers.

The current run has 39,901 training, 9,976 validation and 49,757 test comments.

| Model (held-out test) | Macro-F1 | Toxic precision | Toxic recall | Accuracy |
|---|---|---|---|---|
| Majority baseline | 0.479 | 0.000 | 0.000 | 0.921 |
| BoW Naive Bayes (from scratch = scikit-learn) | 0.667 | 0.482 | 0.309 | 0.919 |
| TF-IDF Logistic Regression | 0.724 | 0.422 | 0.621 | 0.903 |
| **DistilBERT fine-tuned** (selected) | **0.801** | **0.634** | **0.632** | **0.942** |

TF-IDF Logistic Regression's accuracy is below the majority baseline because it trades false positives for toxic recall; DistilBERT is the only model that beats the baseline on accuracy as well. Always show macro-F1 and class-specific metrics alongside accuracy. A TF-IDF Naive Bayes variant was dropped: at the fixed 0.5 threshold it caught under 1% of toxic comments.

## Fine-tuned transformer (DistilBERT)

```powershell
uv pip install --python .venv/Scripts/python.exe torch --index-url https://download.pytorch.org/whl/cu128
uv pip install --python .venv/Scripts/python.exe -r backend/requirements-transformer.txt
./.venv/Scripts/python.exe -m backend.training.train_transformer
```

Run it **after** `backend.training.train`: it adds its row to the same `evaluation.json` (re-running `train` rewrites that file, so re-run the transformer afterwards).

- Same deduplicated train / validation / test split as the classical models (seed 42), so the comparison is like-for-like.
- `distilbert-base-uncased`, 2 epochs, max 128 tokens, batch 16, AdamW lr 3e-5 with linear warm-up, mixed precision, class-weighted loss for the ~8% toxic class.
- The best epoch and the decision threshold (0.64) are chosen on validation macro-F1. Test is scored once afterwards. At the default 0.5 threshold test macro-F1 is also 0.801 (precision 0.614, recall 0.656), so the gain is not a threshold artefact.
- Weights (~260 MB) are saved to `backend/artifacts/transformer/` and are not committed. The backend loads them if present (GPU if available, otherwise CPU) and adds a `transformer_assessment` to every analysed message; scoring a 13-message conversation takes ~15 ms on the GPU.
- Limits: it reads one message at a time, so it does not see conversation context; scores are not calibrated probabilities; English comments only. The context-aware model below addresses the first point.

Exact deduplication does not eliminate near duplicates. Thread/author identifiers are not supplied, so source-thread or author separation cannot be verified. Scores are not calibrated probabilities. English comment performance does not establish chat, sarcasm, demographic fairness or Hindi/Hinglish performance.

The original 10-conversation demo benchmark remains separate. It is a regression demonstration, not evidence of 100% real-world performance.

## Context-aware model (Phase 3, in progress)

Goal: score each message **together with the turns before it**, so "you're an idiot 😂" between joking friends, "please stop" from a victim, and "good, you deserve it" after "I failed my exam" are read correctly.

### Reproduce

```powershell
./.venv/Scripts/python.exe -m backend.training.context_data            # download + convert public datasets
./.venv/Scripts/python.exe -m backend.training.synthetic_conversations # template conversations (stand-in data)
./.venv/Scripts/python.exe -m backend.training.train_context --synthetic --variants message_only context_tags_cf context_no_tags_cf
./.venv/Scripts/python.exe -m backend.training.train_combiner --synthetic
```

Needs the Phase 2 model (`train_transformer`) first. About 1 hour on an RTX 3050 Laptop GPU.

### Data

| Source | What it adds | Licence / terms |
|---|---|---|
| [CCC](https://github.com/ipavlopoulos/context_toxicity) (Xenos et al., 2021) | 9,929 posts with toxicity judged **with and without** the parent post; 678 labels flip when the parent is shown | Apache-2.0 repository |
| [CONDA](https://github.com/usydnlp/CONDA) (Weld et al., 2021) | Dota 2 match chats, turn-level explicit/implicit toxicity, speaker ids | No licence file; used for academic research with citation, not redistributed. Its test split is unlabelled, so its validation split is our test. |
| [DiaSafety](https://github.com/thu-coai/DiaSafety) (Sun et al., 2022) | Context + reply pairs; only *Offending User* and *Toxicity Agreement* kept | Apache-2.0 repository |
| Synthetic (`synthetic_conversations.py`) | 3,000 template conversations (12 scenarios incl. victim replies, bystanders, exclusion, threats, Hinglish) | Generated here |

Splits are grouped by conversation/post, so no conversation is in two splits. Raw and processed data are git-ignored.

**Synthetic data rules.** Every phrase pool is split in half: training conversations use only half A, the synthetic test uses only half B, so that score measures unseen wording. A leakage check rejects the data if any phrase is too close (word-Jaccard ≥ 0.55) to the challenge set; the first draft failed this check (three exact copies) and was reworded. Synthetic chat is cleaner than real chat: treat it as a placeholder until `annotation/gold.jsonl` exists.

### Input format

`[CLS] [OTHER] earlier turn [SAME] earlier turn … [SEP] message being scored [SEP]` — up to 3 previous turns; `[SAME]`/`[OTHER]` say whether the earlier turn has the same author as the scored message (names are never given to the model); oldest context is truncated first. Shared by training and serving in `backend/app/services/context_format.py`.

### Behaviour gate

`backend/training/context_challenge.py` holds 32 hand-written cases (victim replies, bystander defence, neutral messages in toxic threads, banter replies, abuse after a stop request, abuse in calm threads, context-needed cruelty). It is never trained on. A context model is served only if it wrongly flags **≤ 25 %** of the safe replies and catches **≥ 75 %** of the harmful messages. Because the gate decides serving, challenge numbers are not an unbiased test.

### Results (held-out test; threshold and epoch chosen on validation)

| Run | Variant | Public test macro-F1 | DiaSafety F1 | CCC flips acc. | Challenge false flags | Challenge detection | Synthetic held-out F1 |
|---|---|---|---|---|---|---|---|
| 1 | Phase 2 model, no extra training | 0.692 | 0.375 | 0.269 | 0.00 | 0.83 | 0.687 |
| 1 | Message-only | 0.889 | 0.740 | 0.778 | — | — | — |
| 1 | Context + speaker tags | 0.901 | 0.798 | 0.838 | 0.30\* | 0.58\* | — |
| 2 | + counterfactual pairs | 0.897 | 0.799 | 0.833 | 0.35 | 0.67 | — |
| 3 | + 20k general comments replayed | 0.897–0.899 | 0.808–0.820 | 0.769–0.796 | 0.10–0.30 | 0.50–0.58 | — |
| **4** | **Message-only + synthetic** | 0.889 | 0.747 | 0.810 | 0.20 | 0.83 | 0.794 |
| **4** | **Context + tags + counterfactual + synthetic (served)** | 0.895 | 0.788 | **0.861** | **0.15** | 0.75 | **0.810** |
| 4 | Same, no speaker tags | 0.895 | 0.789 | 0.843 | 0.10 | 0.75 | 0.791 |

\* measured after the run on the saved model. Full numbers: `backend/artifacts/context_evaluation*.json`.

What the runs show:

1. **Context helps on public benchmarks** (macro-F1 0.889 → ~0.90, DiaSafety 0.74 → 0.80, CCC flips 0.78 → 0.83–0.86). CONDA (game chat) gains nothing: toxicity there is visible in the message itself.
2. **Benchmark gains hid a safety problem.** Models fine-tuned on the public data wrongly flagged 25–35 % of harmless replies such as "please stop, that's not funny" or "leave her alone". Message-only models trained on the same data did too (30 %), so the cause is the labels treating firm pushback as toxic, not only context leaking into the label. Counterfactual pairs (non-toxic message after an unrelated toxic turn, label kept) and replaying general comments did not fix it.
3. **Synthetic conversations with explicit victim/bystander/banter labels fixed most of it**: false flags 35 % → 15 %, and the context model became the best on CCC flips and on unseen synthetic wording.
4. **Speaker tags and 1 vs 3 turns of context made no measurable difference** (differences ≤ 0.005, the size of GPU run-to-run noise). Only CONDA has same-speaker turns, so these datasets cannot really test tags.
5. **Still weak:** "context needed" cruelty (e.g. "serves you right" after bad news) is caught 1 time in 4 on the challenge set, and some friendly banter is still flagged. Results come from one seed; no confidence intervals yet.

### Learned risk combiner

`backend/app/services/combiner.py` turns one analysis into 48 features (share of each rule label, rule signals, targeting pattern, and the three model scores) and a regularised logistic regression maps them to Low / Moderate / High / Critical. It is shown beside the rule-based risk, never instead of it, and refuses to run if the available models differ from those it was trained with.

Trained on 2,400 synthetic conversations, tested on 600 with unseen wording:

| | Accuracy | Macro-F1 | Quadratic κ |
|---|---|---|---|
| Rules only | 0.490 | 0.286 | 0.266 |
| Learned combiner | **0.708** | **0.651** | **0.570** |

The rules miss reworded threats and exclusion completely (0 % on those scenarios: "you'd better be scared" is read as harmless), which is the brittleness of hand-written patterns. The combiner fixes much of that (targeting 38 % → 92 %, single insults 58 % → 98 %) but over-flags friendly banter (100 % → 63 %) and is still poor on threats (36 %) and context-needed cruelty (13 %). Its cross-validation score on the training phrases (0.95) is inflated because the context model saw those conversations; quote the held-out numbers.

### Next step: real labelled conversations

Collect and label ~300 real conversations with `annotation/GUIDELINES.md` and `python -m backend.training.annotate` (two annotators, Cohen's κ). Then retrain the combiner with `python -m backend.training.train_combiner` on `annotation/gold.jsonl` and use it as the final test set for every model above. Until then, all conversation-level numbers rest on synthetic data.

## WhatsApp text import and report

Open **Import WhatsApp** in the app. Use WhatsApp's Export chat → Without media option and select the resulting `.txt` file. The built-in synthetic sample and `backend/tests/fixtures/whatsapp_project.txt` demonstrate the full workflow without using a private chat.

1. Choose the text export (UTF-8 or UTF-16), select the date order and relationship, and choose whether to mask participant names/contact details.
2. Check the parsing preview. It preserves source order, timestamps, multiline text, Unicode names, and source-line references. Invalid dates and unrecognized headers produce visible warnings. System events and attachment-only messages are counted separately.
3. Analyze and draft the report. Discussion keywords and representative source excerpts use local TF-IDF extraction. No generated decisions or verified allegations are inferred. Sessions split at date changes, gaps of 60 minutes, or 100 text messages; these are not learned semantic topic boundaries.
4. Inspect concern episodes with surrounding replies, message explanations, participant activity, and source links. Search/filter the paginated transcript or jump to a quoted source message.
5. Download a self-contained HTML report or Markdown. Open the HTML in your browser and use Print → Save as PDF if needed. Downloaded reports include evidence, parsing notices, method, and limitations.

This version supports up to **2 MiB of decoded UTF-8 text, 5,000 entries, 100 participants, and 20,000 characters per text message**. The file chooser also caps the uploaded file at 2 MiB. ZIP/media/voice-note/backup import is not implemented. Larger inputs are rejected, not silently truncated. The supported timestamp families are `DD/MM/YYYY, HH:MM - Name: text` and `[DD/MM/YYYY, HH:MM] Name: text`, with an explicit MDY option, optional seconds/AM-PM, and year-first dates.

Risk analysis uses structured messages directly, so Unicode names and source IDs are not lost through the plain-text conversation parser. It reviews 120 new text messages per window with up to 20 preceding and 20 following messages. Each message is counted once in the totals. The overall concern/index is the highest-concern window, not an average: a threat is not diluted by unrelated neutral history. The index remains heuristic, not a measured probability. Context beyond the overlapping windows is not modeled.

Masking replaces participant names/mentions, emails and phone-like strings before analysis/export. It does not guarantee complete anonymization: addresses, unnamed people, unusual identifiers and other personal details may remain. Inspect the preview/report before sharing. Imported content remains in browser memory until removed/refreshed; no server-side chat/report database is created, and no hosted model is called in this workflow. Reported speech, indirect threats, sarcasm and recipient inference retain the limitations of the existing engine.

API endpoints: `POST /api/imports/whatsapp/preview` and `POST /api/imports/whatsapp/analyze`. Both accept JSON with `text`, `date_order`, `anonymize`, and `relationship`; there is no server-side import history.

## Optional hosted review setup

Copy `.env.example` to `.env` and set `HF_TOKEN` and `HF_CHAT_MODEL` on the backend. Do not put credentials in `VITE_*` variables or paste them into the browser. Select a currently available chat model from the [Hugging Face playground](https://huggingface.co/playground); model/provider access and billing depend on your account. The implementation follows the [Hugging Face chat-completion API](https://huggingface.co/docs/inference-providers/tasks/chat-completion).

Restart the backend. Open Language lab → Hosted second opinion. The user reviews the exact text and checks consent before a request is sent. Only that displayed text is sent to Hugging Face and its selected inference provider. No automatic hosted calls occur during normal local analysis. Provider failures, truncated responses, malformed output and invented evidence quotes are rejected. The generated review never overwrites local risk.

No API credentials were supplied during implementation. Protocol and validation are tested with a simulated provider; a real hosted inference call remains unverified until credentials are configured.

## Implemented NLP Laboratory Course Outcomes

ContextGuard now implements full end-to-end demonstrations for all five Course Outcomes:
1. **CO1 (Text Preprocessing):** Clean noise, NFKC normalization, URL/email tokenization, sentence splitting, word/character/BPE/WordPiece tokenization, stopword filtering with negation retention, Porter & Lancaster stemmers, and spaCy lemmatizer.
2. **CO2 (Feature Extraction & Word Representations):** Levenshtein dynamic programming edit distance with traceback, Bag-of-Words and TF-IDF matrices, N-grams (1, 2, 3), and NumPy-based Skip-gram Word2Vec embeddings with negative sampling (cosine similarity, nearest neighbors, analogies $b - a + c$, and corpus retraining).
3. **CO3 (POS Tagging & Named Entity Recognition):** Dual POS tagging featuring both industrial spaCy (`en_core_web_sm`) and an educational First-Order Hidden Markov Model (HMM) trained with Laplace smoothing and decoded using Viterbi dynamic programming; alongside spaCy Named Entity Recognition (PERSON, ORG, GPE, DATE).
4. **CO4 (Text Classification & Evaluation):** Multi-model evaluation benchmark (from-scratch Naive Bayes, scikit-learn Naive Bayes, TF-IDF Logistic Regression) with accuracy, precision, recall, macro-F1, and confusion matrices; combined with ContextGuard's 13-turn contextual cyberbullying detection engine.
5. **CO5 (LLM Integration & Deployment):** Hugging Face Chat Completion API integration for second-opinion review with explicit consent gating, structured Pydantic schema validation, evidence quotation verification, and graceful unconfigured fallbacks.

The main future academic experiment is collecting a larger multi-turn annotated chat corpus with inter-annotator agreement (Cohen's Kappa) across diverse demographics.

Never load untrusted joblib files. Server model paths are fixed to locally generated artifacts; there is no model upload endpoint.
