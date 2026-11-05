# ContextGuard — Academic Demonstration & Viva Preparation Guide

This guide provides a comprehensive, step-by-step walkthrough for demonstrating **ContextGuard (NLP-Based Context-Aware Cyberbullying and Toxicity Detection System)** for an academic presentation or laboratory evaluation.

---

## 1. Quick Startup Instructions

### Method A: One-Click Startup (Recommended)

Open Windows PowerShell in the project directory:
```powershell
cd D:\FSD\NLP-Based-ContextGuard-main
powershell -ExecutionPolicy Bypass -File .\Start-ContextGuard.ps1 -OpenBrowser
```
This script starts both the FastAPI backend and Vite frontend in the background, validates their HTTP health endpoints, and launches your default browser.

### Method B: Manual Two-Terminal Startup

**Terminal 1 — Backend (FastAPI):**
```powershell
cd D:\FSD\NLP-Based-ContextGuard-main
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Swagger Interactive Documentation: `http://127.0.0.1:8000/docs`

**Terminal 2 — Frontend (Vite / React):**
```powershell
cd D:\FSD\NLP-Based-ContextGuard-main\frontend
npm run dev
```
- Web Application: `http://127.0.0.1:5173`

---

## 2. Course Outcomes (CO1–CO5) Experiment Mapping

| Course Outcome | Experiment / Topic | Implementation in ContextGuard | Where to Demonstrate in UI |
|---|---|---|---|
| **CO1** | Text Preprocessing | • HTML & zero-width noise stripping<br>• NFKC Unicode normalization<br>• URL & email tokenization<br>• Sentence segmentation<br>• Word, character, WordPiece (8k), and BPE (8k) tokenizers<br>• Stopword removal with explicit **negation preservation** (`not`, `never`, `n't`)<br>• Porter & Lancaster stemmers vs spaCy lemmatizer | **Language Lab** → **01 / Preprocessing** |
| **CO2** | Feature Extraction & Word Representations | • N-grams (unigram, bigram, trigram)<br>• Levenshtein edit distance with full DP cost matrix and backtrace operations<br>• Manual Bag-of-Words and smoothed TF-IDF matrix builder<br>• Educational Skip-gram Word2Vec (NumPy SGNS) with 32-dim vectors, cosine similarity, nearest neighbors, analogies ($b - a + c$), and corpus retraining | **Language Lab** → **02 / Features & Vectors**<br>**Language Lab** → **03 / Word Embeddings** |
| **CO3** | POS Tagging & Named Entity Recognition | • Industrial spaCy (`en_core_web_sm`) POS tagger and dependency parser<br>• From-scratch First-Order Hidden Markov Model (HMM) POS tagger with Laplace smoothing and Viterbi dynamic programming decoding<br>• Side-by-side POS tagging comparison<br>• Named Entity Recognition (PERSON, ORG, GPE, DATE) with character spans | **Language Lab** → **04 / POS & NER** |
| **CO4** | Text Classification & Evaluation | • From-scratch Multinomial Naive Bayes<br>• Scikit-learn Multinomial Naive Bayes<br>• Scikit-learn TF-IDF Logistic Regression (validation macro-F1: 0.725, test accuracy: 90.3%)<br>• Evaluation metrics: Accuracy, Precision, Recall, Macro-F1, Confusion Matrix, Majority Baseline<br>• 13-turn contextual cyberbullying detection engine | **Language Lab** → **05 / Classification**<br>and **Conversation Analyzer** tab |
| **CO5** | LLM Integration & Deployment | • Hugging Face Chat Completion API client<br>• Explicit user consent gate (no data leakage by default)<br>• Structured Pydantic validation schema<br>• Grounded evidence quotation verification<br>• Graceful fallback when unconfigured | **Language Lab** → **06 / Hosted LLM** |

---

## 3. 10–15 Minute Demonstration Walkthrough Sequence

### Phase 1: Problem Introduction & Architecture (2 minutes)
1. Open `http://127.0.0.1:5173`.
2. **Key Talking Point:** Traditional cyberbullying detection evaluates single comments in isolation using keyword matching or static sentiment models. This fails in two directions:
   - **False Positive on Friendly Banter:** Friends joking (*"You're such an idiot 😂"*) get banned.
   - **False Negative on Subtle Harassment:** Covert ostracism (*"Nobody wants you in this group"*) or targeted repeated insults without profanity go completely undetected.
3. Show the **Methodology** tab highlighting the hybrid architecture: Rule-based multi-turn dialogue dynamics combined with statistical NLP feature extractors.

### Phase 2: Core ContextGuard Conversation Scenarios (3 minutes)
Go to the **Conversation Analyzer** tab and demonstrate key preloaded scenarios:

1. **Scenario 1: Friendly Teasing (Suppression of False Positives)**
   - Click "Friendly Banter" from the preloaded examples.
   - *Input:* Alice: "You're such a genius 😂" / Bob: "Bro, I know. Nobel Prize incoming."
   - *Result:* **Low Risk (Friendly Banter)**.
   - *Explanation:* The laughter anchor (`😂`) and bilateral playful response prevent false positive alerts.

2. **Scenario 2: Repeated Social Exclusion (Detecting Covert Bullying)**
   - Click "Repeated Exclusion".
   - *Input:* Alex repeatedly telling Sam: "Nobody wants you in this group", "Seriously, just leave".
   - *Result:* **High Risk (Possible Cyberbullying)**.
   - *Explanation:* No profanities are used, but persistent unilateral targeting asymmetry triggers high concern.

3. **Scenario 3: Boundary Assertion & Retaliatory Warning**
   - Click "Retaliatory Threat" or "13-Turn Multi-Turn Targeting".
   - Show how ContextGuard distinguishes between the **aggressor** (Jordan), the **victim asserting boundaries** (Sam: *"Please stop calling me that"*), and the **pro-social bystander defending the victim** (Alex: *"Jordan, leave him alone"*).
   - Point out that **bystander defense is NOT marked as aggression**.

4. **Scenario 4: College Project Exclusion & Bystander Intervention (15 Turns)**
   - Click "College Project Exclusion & Retaliatory Intimidation" (Aarav, Rohan, Karan).
   - *Result:* **High Risk (Cyberbullying)**, Risk Score: **88/100**.
   - *Key Highlights for Examiner:*
     - **Turn 4:** Rohan's personal degradation (*"slowing everyone down"*) is identified as harmful rather than neutral.
     - **Turn 7:** Aarav's protest (*"stop making jokes about me"*) is tracked as a victim boundary.
     - **Turn 10:** Rohan's conditional exclusion (*"if you were actually useful"*) recognized as cyberbullying.
     - **Turn 11 & 14:** Karan's interventions (*"This isn't funny anymore. Add him to the group"*) correctly classified as pro-social **Bystander Defence**.
     - **Turn 12:** Rohan's pushback (*"Keep defending him. You'll both get ignored"*) recognized as **Retaliatory Social Intimidation**.
     - **Turn 13:** Aarav's distress (*"don't want to come to college tomorrow"*) recognized as a **Victim Emotional Distress & Avoidance Signal** (evidence of impact, NOT aggression).
     - **Turn 15:** Rohan's refusal (*"still not getting added"*) recognized as **Continued Social Exclusion**.
     - **Role Tracking:** Rohan = Primary Aggressor, Aarav = Primary Target, Karan = Bystander Defender.

---

### Phase 3: NLP Laboratory Demonstration (CO1–CO5) (7 minutes)
Click **Language Lab** in the navigation bar.

#### 1. Tab 01 / Preprocessing (CO1)
- Enter sample text:
  ```html
  <b>Maya</b> told Jordan: "Please stop calling me an idiot." They meet in Mumbai on Friday. Check https://example.com
  ```
- Click **Run Text Inspection**.
- Point out:
  - **Noise Removal:** `<b>` tags stripped, whitespace collapsed.
  - **Normalization:** NFKC Unicode, URL mapped to `URL`.
  - **Multi-Level Tokenization:** Sentence split, word tokens, character tokens, and subword tokens (**WordPiece** and **BPE** with 8,000-token vocabularies).
  - **Stopword Analysis & Negation Preservation:** Show that words like `an`, `the` are removed, while negation words (`not`, `never`, `n't`) are strictly preserved to prevent polarity flipping.
  - **Stemming vs. Lemmatization Table:** Compare **Porter** (*"call"*), **Lancaster** (*"cal"*), and **spaCy Lemma** (*"call"*, preserving morphological integrity).

#### 2. Tab 02 / Features & Vectors (CO2)
- Scroll to **Levenshtein Edit Distance Calculator**:
  - String 1: `cyberbullying`
  - String 2: `cyberbully`
  - Click **Compute Distance**.
  - Show the **Dynamic Programming Cost Matrix** and the exact backtraced sequence of operations (Match, Match... Insert `i`, `n`, `g`).
- Scroll to **Bag of Words & TF-IDF Matrix Builder**:
  - Show the mathematical formula: $\text{TF} \times \text{IDF}_{\text{smoothed}}$.
  - Show the computed term-document matrix across the sample documents.

#### 3. Tab 03 / Word Embeddings (CO2)
- Point out the **Word2Vec Status Card**:
  - Model: Skip-gram with Negative Sampling (SGNS) implemented in pure NumPy.
  - Dimensions: 32 | Window: 2 | Vocabulary: ~146 terms.
- **Cosine Similarity Test:**
  - Word 1: `friend`, Word 2: `peer` $\to$ Cosine similarity $\approx 0.97$ (High semantic similarity).
  - Word 1: `threat`, Word 2: `friend` $\to$ Distant semantic similarity.
- **Nearest Neighbors:**
  - Query: `threat` $\to$ Returns nearest semantically related context words (`attack`, `toxic`, `harm`).
- **Word Analogy ($b - a + c$):**
  - $A: \text{man}, B: \text{king}, C: \text{woman} \to \text{queen}$.
- **Custom Corpus Retraining:** Show that users can paste custom text and retrain the embedding weights dynamically!

#### 4. Tab 04 / POS & NER (CO3)
- Enter: `"Friends protect each other from aggressive bullies."`
- Point out the **Dual POS Tagging Architecture**:
  - **spaCy POS:** Pretrained statistical tagger (`NOUN`, `VERB`, `ADJ`, etc.).
  - **HMM POS (From Scratch):** First-order Hidden Markov Model decoded using **Viterbi Dynamic Programming**, trained on dialogue with Laplace smoothing.
  - Show the **Match Indicator** comparing both taggers.
- Point out **Named Entity Recognition (NER):** Detects entities like `Maya` (`PERSON`), `Mumbai` (`GPE`), `Friday` (`DATE`) with start/end character offsets.

#### 5. Tab 05 / Classification Benchmark (CO4)
- View the held-out validation and test evaluation table:
  - **Baseline:** Majority class baseline.
  - **From-Scratch Naive Bayes:** BoW manual implementation ($F_1 = 0.681$).
  - **Scikit-Learn Naive Bayes:** BoW Gaussian/Multinomial ($F_1 = 0.681$).
  - **TF-IDF Logistic Regression (Selected):** Test Accuracy: $90.3\%$, Macro-$F_1$: $0.724$.
- View the **Confusion Matrix** (True Negatives, False Positives, False Negatives, True Positives).
- **Key Talking Point:** Explain why accuracy ($90.3\%$) is lower than the majority baseline ($91.8\%$) — because cyberbullying is highly imbalanced, and our model prioritizes **toxic recall ($62.1\%$)** over naive majority prediction.

#### 6. Tab 06 / Hosted LLM Review (CO5)
- Show the consent-gated interface: external API calls require explicit operator consent.
- Explain the structured Pydantic schema validation that forces the LLM to output verified direct quotations from the conversation rather than hallucinations.
- Note the graceful unconfigured state when no API key is supplied.

---

### Phase 4: WhatsApp Import & Summary Report (2 minutes)
1. Click **Import WhatsApp** in the top navigation.
2. Select the preloaded synthetic demonstration conversation.
3. Show:
   - Session splitting (based on time deltas and message count).
   - Dynamic masking of participant names and phone numbers for privacy.
   - Export options: **Download Self-Contained HTML Report** and **Download Markdown Report**.

---

## 4. Viva Questions & Theoretical Explanations

### Q1: What is the difference between Porter and Lancaster stemmers?
- **Answer:** The **Porter stemmer** uses a 5-phase cascade of heuristic suffix-stripping rules (e.g., `sses` $\to$ `ss`, `ational` $\to$ `ate`), producing relatively conservative and linguistically intuitive stems. The **Lancaster stemmer** is much more aggressive and iterative, stripping or replacing suffixes rapidly. This can lead to heavy over-stemming (e.g., reducing *"calling"* to *"cal"*), whereas lemmatization uses dictionary lookup and morphological analysis via POS tags to preserve the true dictionary root (lemma).

### Q2: How does Word2Vec Skip-gram with Negative Sampling (SGNS) work?
- **Answer:** Given a sequence of words $w_1, w_2, \dots, w_T$, the Skip-gram architecture maximizes the probability of predicting context words within a window $c$ given a center target word $w_t$:
  $$\mathcal{L} = \sum_{t=1}^T \sum_{-c \le j \le c, j \ne 0} \log P(w_{t+j} \mid w_t)$$
  To avoid calculating the expensive softmax denominator over the entire vocabulary $V$, **Negative Sampling** replaces it with binary logistic regression:
  $$\log \sigma(v'_{w_O}{}^\top v_{w_I}) + \sum_{k=1}^K \mathbb{E}_{w_k \sim P_n(w)} [\log \sigma(-v'_{w_k}{}^\top v_{w_I})]$$
  where $K$ noise words are drawn from the unigram distribution raised to the $3/4$ power ($P(w)^{0.75}$).

### Q3: How does the Viterbi algorithm decode the optimal POS tag sequence in an HMM?
- **Answer:** An HMM models $P(W, T) = \prod_{i=1}^n P(t_i \mid t_{i-1}) P(w_i \mid t_i)$. The Viterbi algorithm is a dynamic programming algorithm that finds $\arg\max_T P(W, T)$ in $O(N \cdot |T|^2)$ time instead of exponential $O(|T|^N)$:
  1. **Initialization:** $V_0(j) = \pi_j \cdot B_j(w_0)$
  2. **Recurrence:** $V_t(j) = \max_{i \in \text{Tags}} [V_{t-1}(i) \cdot A_{ij}] \cdot B_j(w_t)$
  3. **Backpointer:** $Backtrace_t(j) = \arg\max_{i \in \text{Tags}} [V_{t-1}(i) \cdot A_{ij}]$
  4. **Termination & Backtracking:** Trace back from the highest-scoring final state to retrieve the most probable sequence of tags.
  In our implementation, computations are performed in log-space ($\log P$) to prevent arithmetic underflow.

### Q4: Why is Laplace (add-$\alpha$) smoothing necessary in HMMs and Naive Bayes?
- **Answer:** Without smoothing, if a word $w$ was never observed with tag $t$ in the training corpus, the emission probability $P(w \mid t) = 0$. Since probabilities are multiplied along the sequence, a single zero probability would force the entire sequence likelihood to zero. Laplace smoothing adds a pseudocount $\alpha$ (typically $\alpha=1$):
  $$P(w \mid t) = \frac{C(t, w) + \alpha}{C(t) + \alpha \cdot (|V| + 1)}$$
  guaranteeing non-zero probabilities for all transitions and emissions.

### Q5: What is the Levenshtein distance recurrence relation?
- **Answer:** Given strings $s_1$ of length $m$ and $s_2$ of length $n$, the distance $D(i, j)$ is computed as:
  $$D(i, j) = \min \begin{cases}
  D(i-1, j) + 1 & \text{(Deletion)} \\
  D(i, j-1) + 1 & \text{(Insertion)} \\
  D(i-1, j-1) + \text{cost} & \text{(Match: cost=0, Substitution: cost=1)}
  \end{cases}$$
  Base cases: $D(i, 0) = i$ and $D(0, j) = j$. ContextGuard renders this full $(m+1) \times (n+1)$ matrix and traces back the exact character edit path.

---

## 5. Verification Commands Summary

To prove system integrity during the demonstration:

```powershell
# Run the complete test suite (186 tests)
.\.venv\Scripts\pytest -v backend\tests

# Run only Course Outcomes coverage tests (11 tests)
.\.venv\Scripts\pytest -v backend\tests\test_co_coverage.py

# Verify frontend production build
npm --prefix frontend run build
```

---

*ContextGuard is developed for academic demonstration and decision support.*

