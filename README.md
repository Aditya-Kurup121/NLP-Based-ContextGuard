# ContextGuard — Context-Aware Cyberbullying Detector

Current setup and reproducible experiments: [NLP guide](NLP_GUIDE.md). Start both preview services with `./Start-ContextGuard.ps1`.

**WhatsApp import:** open Import WhatsApp to preview a text export, mask participant names, review discussion sessions and source-linked concern episodes, and download an HTML/Markdown report. Parsing warnings and exclusions remain visible. The importer uses local extraction and risk analysis; no API key or hosted model is needed. See the guide for input limits and supported formats.

The Language lab provides POS/NER, word/character/WordPiece/BPE tokenization, stemming/lemmatization, manual BoW/TF-IDF, and held-out classifier comparisons. Conversation risk is rule-based; learned comment toxicity is shown separately. The selected Logistic Regression model achieves test macro-F1 **0.724**, toxic precision **0.422**, and toxic recall **0.621** on **49,757** held-out public comments. The optional hosted LLM second opinion needs backend credentials and explicit user consent; no live hosted call has been verified.

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
C:\Users\Aditya\Downloads\NLPP\NLPP\
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py         # REST endpoints (health, examples, analyze, evaluate, model-info)
│   │   ├── schemas/
│   │   │   └── analysis.py       # Pydantic request, response, and metric schemas
│   │   ├── services/
│   │   │   ├── parser.py         # Multi-format turn parser (Speaker: Text, Timestamps, Brackets)
│   │   │   ├── features.py       # Laughter, exclusion, threat, sarcasm, and target extractors
│   │   │   ├── engine.py         # ContextGuard analysis engine with calibrated heuristics
│   │   │   ├── examples.py       # Preloaded test demonstrations
│   │   │   └── evaluator.py      # Automated benchmark & confusion matrix generator
│   │   └── main.py               # FastAPI application entry point with CORS
│   ├── tests/
│   │   ├── test_parser.py        # Dialogue format parsing tests
│   │   ├── test_engine.py        # Core scenario validation (Banter, Exclusion, Sarcasm, Threats)
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
│   │   │   └── BenchmarkSection.tsx
│   │   ├── services/
│   │   │   └── api.ts            # Client API methods
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript interfaces
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Quickstart & Execution Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Node.js 18+ (Tested on Node.js v22)

---

### Step A: Start Backend Server

1. Open a terminal in the project root:
   ```powershell
   cd C:\Users\Aditya\Downloads\NLPP\NLPP
   ```

2. Activate virtual environment (or create one):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   # Or on Linux/macOS: source venv/bin/activate
   ```

3. Install dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```

4. Start FastAPI with Uvicorn:
   ```powershell
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

Backend will be active at:
- **API URL:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`

---

### Step B: Start Frontend Development Server

1. Open a second terminal:
   ```powershell
   cd C:\Users\Aditya\Downloads\NLPP\NLPP\frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Start Vite dev server:
   ```powershell
   npm run dev
   ```

4. Open browser at:
   - `http://localhost:5173`

---

## 4. Preloaded Demonstration Scenarios

| Scenario | Input Conversation | Expected Analysis Outcome | Contextual Reason |
| :--- | :--- | :--- | :--- |
| **1. Friendly Banter** | `Alice: You're such a genius 😂`<br>`Bob: Bro, I know. Nobel Prize incoming.`<br>`Alice: Don't forget us when you're famous.` | **Low Risk (Friendly Banter)** | Reciprocal humor and laughter anchors suppress false alarm despite teasing phrasing. |
| **2. Repeated Exclusion** | `Alex: Nobody wants you in this group.`<br>`Alex: Seriously, just leave.`<br>`Alex: Everyone here would be happier without you.` | **High Risk (Possible Cyberbullying)** | Persistent unreciprocated ostracism and repeated targeting asymmetry ($3\times$ hostile turns). |
| **3. Sarcasm & Ambiguity** | `Sam: Wow, you're a real genius.`<br>`Jordan: What is that supposed to mean?`<br>`Sam: Forget it.` | **Moderate Risk (Potentially Harmful)** | Sarcastic praise followed by recipient distress; preserved uncertainty due to incomplete history. |
| **4. Physical Threat** | `Taylor: I'm going to find you after class and hurt you.` | **Critical Concern (Threat / Urgent Concern)** | Direct physical threat triggers safety protocol, evidence preservation, and adult reporting advice. |
| **5. Retaliatory Threat** | `Nikhil: Why did you report my account?`<br>`Vivek: You kept sending me abusive messages...`<br>`Nikhil: You're going to regret doing that.`<br>`Nikhil: I'll find you after college tomorrow.` | **High Risk (Confrontation Threat)** | Retaliatory escalation with specific future timeframe following abuse report, persisting past boundaries. |
| **6. 13-Turn Multi-Turn Targeting** | `Jordan: You're such an idiot...`<br>`Sam: That's not fair, please stop.`<br>`Jordan: Loser. Nobody even likes you here...`<br>`Alex: Jordan, come on, cut it out...` | **High Risk (Asymmetric Cyberbullying)** | Captures repeated insults, victim stop requests, retaliatory threats, and pro-social bystander defense. |

---

## 5. Automated Testing & Benchmark Evaluation

### Run Backend Unit & Regression Tests (Pytest)
```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\pytest -v backend\tests
```
**157 passed tests** covering:
- **Parser formats:** Standard colon, timestamps, brackets, multiline continuations, unlabeled blocks
- **Core Engine:** Banter suppression, social exclusion, sarcasm calibration, lethal threats
- **Threat Detection (Scenarios A–G):** Confrontation threats, boundary assertions, retaliatory warnings
- **ContextGuard 13-Turn Regression:** Feature extraction, target attribution, per-turn classification, targeting matrix, aggregate risk synthesis
- **Runtime Workplace Exclusion & Bystander Defense:** Covert ostracism, defender challenge, boundary dismissal, bystander defense, counterexamples, and silent-ignoral guardrails
- **API Endpoints:** Health, demonstration retrieval, model metadata, multi-turn analysis, benchmark evaluation

### Run Benchmark Evaluation Script
```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\python -m backend.app.services.evaluator
```
Reports metrics on 10 curated synthetic demonstration conversations. These are regression examples; use Language lab → Model evidence for the separate held-out public-comment evaluation.

### Build Frontend Production Bundle
```powershell
cd frontend
npm run build
```

---

## 6. Privacy, Ethics & Decision-Support Standard

- **Local by default:** Conversation review and the language lab run on the configured local backend without sending text to a model provider. The separate hosted-review action sends only the displayed transcript to Hugging Face after explicit consent.
- **Decision-Support Guardrail:** ContextGuard provides risk estimates and plain-English indicators to assist human discernment; it **must never be used as an automated judge for unilateral disciplinary expulsion**.
- **Dataset Privacy:** Benchmark samples are synthetic, ethically constructed scenarios free of non-consensual personal identifiable information (PII).

