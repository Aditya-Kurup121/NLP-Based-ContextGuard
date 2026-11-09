# ContextGuard — Context-Aware Cyberbullying Detector

Current setup and reproducible experiments: [NLP guide](NLP_GUIDE.md). Start both preview services with `./Start-ContextGuard.ps1`.

**WhatsApp import:** open Import WhatsApp to preview a text export, mask participant names, review discussion sessions and source-linked concern episodes, and download an HTML/Markdown report. Parsing warnings and exclusions remain visible. The importer uses local extraction and risk analysis; no API key or hosted model is needed. See the guide for input limits and supported formats.

The Language lab provides POS/NER, word/character/WordPiece/BPE tokenization, stemming/lemmatization, manual BoW/TF-IDF, and held-out classifier comparisons. Conversation risk is rule-based; learned comment toxicity is shown separately. On **49,757** held-out public comments, a fine-tuned **DistilBERT** reaches test macro-F1 **0.801** (toxic precision **0.634**, recall **0.632**), up from **0.724** for the TF-IDF Logistic Regression baseline (precision 0.422, recall 0.621). Both models score messages one at a time and are shown beside the rule-based conversation risk; neither overrides it. A **context-aware DistilBERT** also reads each message with its previous 3 turns (trained on CCC, CONDA, DiaSafety and synthetic conversations; served only after passing a 32-case behaviour test), and a **learned risk combiner** gives a second-opinion risk level. Both currently rest partly on synthetic data — see the NLP guide. The optional hosted LLM second opinion needs backend credentials and explicit user consent; no live hosted call has been verified.

> **"Understand the context. Detect the harm."**

ContextGuard is an assistive, full-stack decision-support platform designed to analyze multi-turn conversations rather than isolated keywords. It evaluates conversational history, reciprocal banter, power imbalance, sarcasm, and repeated targeting to provide transparent, explainable assessments.

---

## 1. Problem Statement & Contextual Solution

Traditional cyberbullying and toxicity filters inspect messages in isolation. This introduces two severe systemic failure modes:
1. **False Positives on Friendly Banter:** Friends joking with phrases like *"You're such an idiot 😂"* or *"Rematch right now loser"* are misflagged as toxic harassers.
2. **False Negatives on Subtle Harassment:** Covert bullying expressed through systematic social exclusion (*"Nobody wants you in this group"*, *"Seriously, just leave"*), coded passive belittling, or targeted piling-on goes completely undetected because no explicit profanities are used.

### The ContextGuard Architecture
ContextGuard processes conversational dynamics across sequential dialogue turns:
- **Laughter & Reciprocal Banter Anchors:** Interlocutors sharing laughter emojis (`😂`, `💀`, `lmao`) and reciprocal counter-teasing suppresses false positives.
- **Sarcasm Calibration & Preserved Uncertainty:** Inverted praise (e.g., *"Wow, you're a real genius."*) is assessed in conjunction with subsequent recipient distress (*"What is that supposed to mean?"*). If ambiguous, it remains honestly classified as `Uncertain — More Context Needed`.
- **Targeting Asymmetry:** Tracks directional utterances ($\text{Source} \to \text{Target}$) to detect unilateral repeated harassment versus bilateral debate.
- **Calibrated Explainability:** Every turn receives plain-English evidence, alternative interpretations, and proportionate next steps.

---

## 2. System Architecture

```text
NLP-Based-ContextGuard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py         # REST endpoints (health, examples, analyze, evaluate, model-info)
│   │   │   ├── nlp_routes.py     # NLP workbench API (inspect, vectorize, Levenshtein, Word2Vec, HMM)
│   │   │   └── import_routes.py  # WhatsApp chat export preview and report API
│   │   ├── schemas/
│   │   │   └── analysis.py       # Pydantic request, response, and metric schemas
│   │   ├── services/
│   │   │   ├── parser.py         # Multi-format turn parser (Speaker: Text, Timestamps, Brackets)
│   │   │   ├── features.py       # Laughter, exclusion, threat, sarcasm, and target extractors
│   │   │   ├── engine.py         # ContextGuard analysis engine with calibrated heuristics
│   │   │   ├── nlp.py            # Preprocessing, spaCy POS/NER, subwords, classifier, manual BoW/TF-IDF
│   │   │   ├── levenshtein.py    # Levenshtein dynamic programming edit distance & alignment
│   │   │   ├── word2vec.py       # Educational NumPy Skip-gram Word2Vec (SGNS), cosine similarity, analogies
│   │   │   ├── hmm_tagger.py     # First-order HMM POS tagger with Laplace smoothing & Viterbi decoding
│   │   │   ├── evaluator.py      # Automated benchmark & confusion matrix generator
│   │   │   ├── hosted.py         # Hugging Face hosted review with schema validation & quote checking
│   │   │   ├── transformer.py    # Fine-tuned DistilBERT toxicity scoring (optional, loads if trained)
│   │   │   └── whatsapp.py       # WhatsApp chat parser, sessionizer, anonymizer, and report generator
│   │   └── main.py               # FastAPI application entry point with CORS
│   ├── artifacts/                # Trained model joblibs, tokenizers, evaluation.json
│   ├── tests/
│   │   ├── test_co_coverage.py   # CO1-CO5 full capability verification suite
│   │   ├── test_nlp_workbench.py # Workbench endpoint & vectorization tests
│   │   ├── test_parser.py        # Dialogue format parsing tests
│   │   ├── test_engine.py        # Core scenario validation (Banter, Exclusion, Sarcasm, Threats)
│   │   ├── test_threat_detection.py # Threat scenarios & boundary assertions
│   │   └── test_api.py           # Endpoint integration & error validation tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── LandingHero.tsx
│   │   │   ├── AnalyzerForm.tsx
│   │   │   ├── RiskSummaryCard.tsx
│   │   │   ├── ConversationTimeline.tsx
│   │   │   ├── MessageDetailModal.tsx
│   │   │   ├── InteractionMatrix.tsx
│   │   │   ├── MethodologySection.tsx
│   │   │   ├── BenchmarkSection.tsx
│   │   │   ├── NlpWorkbench.tsx   # 6-tab interactive NLP laboratory for CO1-CO5
│   │   │   └── WhatsAppImport.tsx # WhatsApp import and PDF/HTML report generator
│   │   ├── services/
│   │   │   ├── api.ts            # Core analysis API methods
│   │   │   └── nlp.ts            # NLP workbench API client
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── Start-ContextGuard.ps1        # One-click startup script for backend & frontend
├── NLP_GUIDE.md                  # Comprehensive NLP experiments & reproducibility guide
├── DEMO_GUIDE.md                 # 10-15 minute presentation walkthrough & viva preparation
└── README.md
```

---

## 3. Quickstart & Execution Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Node.js 18+ (Tested on Node.js v22)

---

### Step A: Start Backend Server

1. Open a terminal in the project root (the folder containing this README).

2. Create and activate a virtual environment, then install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
   .\.venv\Scripts\Activate.ps1
   # Or on Linux/macOS: source .venv/bin/activate
   ```

3. Start FastAPI with Uvicorn:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```

Backend will be active at:
- **API URL:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`

---

### Step B: Start Frontend Development Server

1. Open a second terminal in the `frontend` folder.

2. Install packages and start the Vite dev server:
   ```powershell
   npm install
   npm run dev
   ```

3. Open browser at:
   - `http://localhost:5173`

*(Alternatively, run `.\Start-ContextGuard.ps1` from the project root to start both backend and frontend servers in one command).*

**Deploying online:** frontend on Vercel, backend on a Hugging Face Space, weights on the Hugging Face Hub. Step-by-step in [DEPLOY.md](DEPLOY.md).

---

## 4. NLP Laboratory Course Outcomes (CO1–CO5) Mapping

| Outcome | Syllabus Topic | Implemented in ContextGuard |
|---|---|---|
| **CO1** | Text Preprocessing | Text noise cleaning (HTML, zero-width chars), NFKC Unicode normalization, URL/email tokenization, sentence splitting, word/character/BPE/WordPiece subword tokenization, stopword removal with negation preservation, Porter & Lancaster stemming vs spaCy lemmatization. |
| **CO2** | Feature Extraction & Word Representations | Handcrafted conversation features (laughter, hostility, targeting), N-grams (1, 2, 3), Levenshtein dynamic programming edit distance with backtrace matrix, manual Bag-of-Words and smoothed TF-IDF matrices, and NumPy Skip-gram Word2Vec (SGNS) embeddings with cosine similarity, nearest neighbors, analogies, and custom corpus retraining. |
| **CO3** | POS Tagging & NER | Dual POS tagging: industrial spaCy (`en_core_web_sm`) alongside an educational from-scratch First-Order Hidden Markov Model (HMM) tagger with Laplace smoothing and Viterbi dynamic programming decoding; plus spaCy Named Entity Recognition (PERSON, ORG, GPE, DATE). |
| **CO4** | Text Classification & Evaluation | From-scratch Multinomial Naive Bayes, scikit-learn Naive Bayes, TF-IDF Logistic Regression, and a fine-tuned DistilBERT transformer (macro-F1 0.801 vs 0.724), all compared on the same held-out split; model performance evaluation (accuracy, precision, recall, macro-F1, confusion matrix, majority baseline); integrated into ContextGuard's 13-turn contextual cyberbullying detection engine. |
| **CO5** | LLM Integration & Deployment | Hugging Face Chat Completion API integration for second-opinion review with explicit consent gating, structured Pydantic schema validation, evidence quotation verification, and graceful unconfigured fallbacks; complete local and production deployment via FastAPI and Vite. |

---

## 5. Preloaded Demonstration Scenarios

| Scenario | Input Conversation | Expected Analysis Outcome | Contextual Reason |
| :--- | :--- | :--- | :--- |
| **1. Friendly Banter** | `Alice: You're such a genius 😂`<br>`Bob: Bro, I know. Nobel Prize incoming.`<br>`Alice: Don't forget us when you're famous.` | **Low Risk (Friendly Banter)** | Reciprocal humor and laughter anchors suppress false alarm despite teasing phrasing. |
| **2. Repeated Exclusion** | `Alex: Nobody wants you in this group.`<br>`Alex: Seriously, just leave.`<br>`Alex: Everyone here would be happier without you.` | **High Risk (Possible Cyberbullying)** | Persistent unreciprocated ostracism and repeated targeting asymmetry ($3\times$ hostile turns). |
| **3. Sarcasm & Ambiguity** | `Sam: Wow, you're a real genius.`<br>`Jordan: What is that supposed to mean?`<br>`Sam: Forget it.` | **Moderate Risk (Potentially Harmful)** | Sarcastic praise followed by recipient distress; preserved uncertainty due to incomplete history. |
| **4. Physical Threat** | `Taylor: I'm going to find you after class and hurt you.` | **Critical Concern (Threat / Urgent Concern)** | Direct physical threat triggers safety protocol, evidence preservation, and adult reporting advice. |
| **5. Retaliatory Threat** | `Nikhil: Why did you report my account?`<br>`Vivek: You kept sending me abusive messages...`<br>`Nikhil: You're going to regret doing that.`<br>`Nikhil: I'll find you after college tomorrow.` | **High Risk (Confrontation Threat)** | Retaliatory escalation with specific future timeframe following abuse report, persisting past boundaries. |
| **6. 13-Turn Multi-Turn Targeting** | `Jordan: You're such an idiot...`<br>`Sam: That's not fair, please stop.`<br>`Jordan: Loser. Nobody even likes you here...`<br>`Alex: Jordan, come on, cut it out...` | **High Risk (Asymmetric Cyberbullying)** | Captures repeated insults, victim stop requests, retaliatory threats, and pro-social bystander defense. |

---

## 6. Automated Testing & Benchmark Evaluation

### Run Backend Unit & Regression Tests (Pytest)
```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\pytest -v backend\tests
```
**193 passed tests** covering:
- **College Project Cyberbullying Suite (`test_college_project_regression.py`):** 15-turn multi-turn exclusion, personal degradation, stop request boundary assertions, distress signals, bystander intervention, retaliatory social intimidation, and benign counterexamples
- **CO Coverage Suite (`test_co_coverage.py`):** Noise cleaning, normalization, negation preservation, Levenshtein DP edit distance, Word2Vec embeddings and analogies, HMM Viterbi POS tagging, classifier status, and banter/threat boundary verification
- **Parser formats (`test_parser.py`):** Standard colon, timestamps, brackets, multiline continuations, unlabeled blocks
- **Core Engine (`test_engine.py`):** Banter suppression, social exclusion, sarcasm calibration, lethal threats
- **Threat Detection (`test_threat_detection.py`):** Confrontation threats, boundary assertions, retaliatory warnings
- **ContextGuard 13-Turn Regression (`test_context_guard_regression.py`):** Feature extraction, target attribution, per-turn classification, targeting matrix, aggregate risk synthesis
- **Runtime Workplace Exclusion & Bystander Defense (`test_runtime_exclusion_repair.py`):** Covert ostracism, defender challenge, boundary dismissal, bystander defense, counterexamples, and silent-ignoral guardrails
- **WhatsApp Import & Privacy Suite (`test_whatsapp_import.py`):** Android/iOS parsing, Unicode speakers, anonymization, size limits, and security
- **API Endpoints (`test_api.py`, `test_nlp_workbench.py`):** Health, demonstration retrieval, model metadata, multi-turn analysis, benchmark evaluation, and all NLP lab routes

### Run Benchmark Evaluation Script
```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\python -m backend.app.services.evaluator
```
Reports metrics on 10 curated synthetic regression examples (the "Regression examples" tab in the app). They are not an evaluation; use Language lab → Model evidence for the separate held-out public-comment evaluation.

### Build Frontend Production Bundle
```powershell
cd frontend
npm run build
```

---

## 7. Privacy, Ethics & Decision-Support Standard

- **Local by default:** Conversation review and the language lab run on the configured local backend without sending text to a model provider. The separate hosted-review action sends only the displayed transcript to Hugging Face after explicit consent.
- **Decision-Support Guardrail:** ContextGuard provides risk estimates and plain-English indicators to assist human discernment; it **must never be used as an automated judge for unilateral disciplinary expulsion**.
- **Dataset Privacy:** Benchmark samples are synthetic, ethically constructed scenarios free of non-consensual personal identifiable information (PII).

