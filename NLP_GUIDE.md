# ContextGuard: NLP experiments and reproducibility

## Run the project

From this project directory, run `./Start-ContextGuard.ps1`. It starts the backend and frontend in hidden processes, checks both HTTP endpoints, and prints the preview URL. Add `-OpenBrowser` to open your default browser. It uses the bundled Node runtime when available, avoiding this machine's unsupported Node 22.11 runtime.

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

These workloads run on CPU. An RTX 3050 is not required. No GPU VRAM size is assumed. This implementation does not install large transformer weights or claim to fine-tune an LLM.

## What is implemented

| Outcome | Demonstrable work |
|---|---|
| CO1 | Regex parsing, normalization preserving negation/emojis, word/character/WordPiece/BPE tokenization, stopword filtering, Porter and Lancaster stems, spaCy lemmas, vocabulary counts |
| CO2 | Handcrafted conversation features, unigram/bigram/trigram inspection, manual BoW and smoothed TF-IDF matrix, trained BoW/TF-IDF classifiers |
| CO3 | A pretrained spaCy English model provides POS tags, dependency heads, noun chunks and named entities with original-text spans |
| CO4 | From-scratch multinomial Naive Bayes, sklearn Naive Bayes, TF-IDF Logistic Regression; validation-selected model; held-out metrics and a majority baseline |
| CO5 | Optional hosted LLM second-opinion endpoint, explicit consent, bounded/validated structured output and exact-quote verification; needs a provider token and a model before live use |

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

The current run has 39,901 training, 9,976 validation and 49,757 test comments. Selected TF-IDF Logistic Regression: test macro-F1 0.724, toxic precision 0.422, toxic recall 0.621. Accuracy is 0.903, lower than the majority baseline's accuracy because it trades false positives for toxic recall. Always show macro-F1 and class-specific metrics alongside accuracy.

Exact deduplication does not eliminate near duplicates. Thread/author identifiers are not supplied, so source-thread or author separation cannot be verified. Scores are not calibrated probabilities. English comment performance does not establish chat, sarcasm, demographic fairness or Hindi/Hinglish performance.

The original 10-conversation demo benchmark remains separate. It is a regression demonstration, not evidence of 100% real-world performance.

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

## Remaining academic experiments

The main next experiment needs independently labeled, multi-turn conversations, including friendly teasing, genuine threats, exclusion, quotations, negation and bystander defense. Keep related conversations, templates and paraphrases in the same split. Have two reviewers label a subset and resolve disagreement. Compare isolated-message and context-aware decisions on the same labels. Keep that evaluation separate from public comment toxicity.

Model fine-tuning, learned conversation representations, probability calibration, fairness evaluation, multilingual support and measured preprocessing ablations are extensions, not current claims. NER/POS currently use a pretrained model; no HMM/CRF is trained here. No Word2Vec/CBOW/Skip-gram implementation is claimed.

Never load untrusted joblib files. Server model paths are fixed to locally generated artifacts; there is no model upload endpoint.
