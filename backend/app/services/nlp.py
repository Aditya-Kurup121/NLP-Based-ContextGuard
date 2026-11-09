"""Inspectable linguistic analysis, local trained statistical classifier, HMM tagger, and Word2Vec."""
import html
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

from backend.app.services.hmm_tagger import get_hmm_tagger
from backend.app.services.transformer import classify_texts_transformer

ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"


def clean_text_noise(text: str) -> str:
    """Removes HTML entities, tags, zero-width characters and excessive whitespace."""
    # Unescape HTML entities (&amp; -> &)
    cleaned = html.unescape(text)
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Strip zero-width and invisible control characters
    cleaned = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u202a\u202c]", "", cleaned)
    # Collapse multiple whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize(text: str) -> str:
    """Preserves emojis, punctuation and negation. Replaces URLs and emails with markers."""
    text = clean_text_noise(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"https?://\S+", " URL ", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", " EMAIL ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


@lru_cache(maxsize=1)
def linguistic_model():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except (ImportError, OSError):
        return None


@lru_cache(maxsize=1)
def classifier():
    path = ARTIFACTS / "toxicity.joblib"
    if not path.exists():
        return None
    import joblib
    return joblib.load(path)


@lru_cache(maxsize=2)
def subword_tokenizer(name: str):
    path = ARTIFACTS / f"{name}.tokenizer.json"
    if not path.exists():
        return None
    from tokenizers import Tokenizer
    return Tokenizer.from_file(str(path))


def classify_texts(texts):
    model = classifier()
    if model is None:
        return [None for _ in texts]
    if not texts:
        return []
    vectorizer = model.named_steps["vectorizer"]
    estimator = model.named_steps["classifier"]
    vectors = vectorizer.transform(texts)
    classes = list(estimator.classes_)
    positive = classes.index(1)
    probabilities = estimator.predict_proba(vectors)[:, positive]
    names = vectorizer.get_feature_names_out()
    # Contributions explain the model's toxic log-odds, not causation or intent.
    weights = estimator.coef_[0] if hasattr(estimator, "coef_") else estimator.feature_log_prob_[positive] - estimator.feature_log_prob_[classes.index(0)]
    result = []
    for row, probability in zip(vectors, probabilities):
        terms = sorted(
            [(names[index], float(value * weights[index])) for index, value in zip(row.indices, row.data)],
            key=lambda pair: abs(pair[1]), reverse=True,
        )[:6]
        result.append({
            "label": "toxic" if probability >= 0.5 else "not toxic",
            "toxicity_score": round(float(probability), 4),
            "model": type(estimator).__name__,
            "top_features": [{"term": term, "contribution": round(value, 4)} for term, value in terms],
            "note": "Standalone comment model; score is uncalibrated and does not establish bullying or intent.",
        })
    return result


def inspect_text(text: str):
    from nltk.stem import PorterStemmer, LancasterStemmer
    nlp = linguistic_model()
    cleaned = clean_text_noise(text)
    normalized = normalize(text)
    words = re.findall(r"\w+(?:['’]\w+)*|[^\w\s]", normalized)
    raw_words = re.findall(r"\w+(?:['’]\w+)*|[^\w\s]", text)
    porter, lancaster = PorterStemmer(), LancasterStemmer()

    entities, tokens, chunks, sentences = [], [], [], []
    if nlp:
        doc = nlp(text)  # Original case and punctuation are essential for NER & sentences
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        tokens = [
            {
                "text": t.text,
                "lemma": t.lemma_,
                "pos": t.pos_,
                "tag": t.tag_,
                "dependency": t.dep_,
                "head": t.head.text,
                "is_stop": bool(t.is_stop),
                "start": t.idx,
                "end": t.idx + len(t),
            }
            for t in doc if not t.is_space
        ]
        entities = [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]
        chunks = [{"text": chunk.text, "root": chunk.root.text} for chunk in doc.noun_chunks]

    if not sentences:
        # Fallback sentence tokenizer using regex
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()] or [text]

    # Stopword identification with negation retention
    negation = {"not", "no", "never", "n't", "n’t", "cannot", "hardly", "barely", "scarcely"}
    removed_stopwords = []
    preserved_negations = []
    filtered = []

    if tokens:
        for t in tokens:
            word_lower = t["text"].lower()
            if word_lower in negation:
                preserved_negations.append(t["text"])
                filtered.append(t["text"])
            elif t["is_stop"]:
                removed_stopwords.append(t["text"])
            else:
                filtered.append(t["text"])
    else:
        # Fallback if spaCy is not available
        common_stops = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and", "or"}
        for w in words:
            if w.lower() in negation:
                preserved_negations.append(w)
                filtered.append(w)
            elif w.lower() in common_stops:
                removed_stopwords.append(w)
            else:
                filtered.append(w)

    # Subword tokenization using BPE and WordPiece
    tokenization_dict = {
        "sentences": sentences,
        "word_and_punctuation": words,
        "raw_words": raw_words,
        "characters": list(text),
    }
    for name in ("wordpiece", "bpe"):
        tokenizer = subword_tokenizer(name)
        tokenization_dict[name] = tokenizer.encode(text).tokens if tokenizer else None

    # HMM POS tagging with Viterbi decoding
    hmm = get_hmm_tagger()
    token_strings = [t["text"] for t in tokens] if tokens else words
    hmm_tags, hmm_log_score, _ = hmm.viterbi(token_strings)

    # Combined POS comparison
    pos_comparison = []
    for i, tok_str in enumerate(token_strings):
        spacy_tag = tokens[i]["pos"] if tokens and i < len(tokens) else "UNK"
        hmm_tag = hmm_tags[i] if i < len(hmm_tags) else "UNK"
        pos_comparison.append({
            "token": tok_str,
            "spacy_pos": spacy_tag,
            "hmm_pos": hmm_tag,
            "match": (spacy_tag == hmm_tag) if spacy_tag != "UNK" else True,
        })

    return {
        "original": text,
        "noise_removed": cleaned,
        "normalized": normalized,
        "tokenization": tokenization_dict,
        "tokens": tokens,
        "entities": entities,
        "noun_chunks": chunks,
        "stemming": {
            "porter": [porter.stem(w) for w in words],
            "lancaster": [lancaster.stem(w) for w in words],
        },
        "stopword_analysis": {
            "filtered_text": " ".join(filtered),
            "removed_stopwords": list(dict.fromkeys(removed_stopwords)),
            "preserved_negations": list(dict.fromkeys(preserved_negations)),
        },
        "stopword_filtered": filtered,
        "vocabulary": {
            "original": len(set(words)),
            "noise_cleaned": len(set(re.findall(r"\w+", cleaned.lower()))),
            "porter": len({porter.stem(w) for w in words}),
            "lancaster": len({lancaster.stem(w) for w in words}),
            "lemmatized": len({t["lemma"] for t in tokens}) if tokens else None,
        },
        "ngrams": {
            str(n): [" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))][:100]
            for n in (1, 2, 3)
        },
        "regex_entities": {
            "urls": re.findall(r"https?://\S+", text),
            "emails": re.findall(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", text),
            "mentions": re.findall(r"(?<!\w)@[\w]+", text),
            "dates": re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text),
        },
        "hmm_pos_tagging": {
            "tags": hmm_tags,
            "log_likelihood": hmm_log_score,
            "model_type": "First-Order HMM with Viterbi Decoding and Laplace Smoothing",
            "pos_comparison": pos_comparison,
        },
        "linguistic_model": "en_core_web_sm" if nlp else None,
        "linguistic_status": "loaded" if nlp else "Install the en_core_web_sm model for POS, lemmas and NER.",
        "classifier": classify_texts([text])[0],
        "transformer": classify_texts_transformer([text])[0],
        "notes": [
            "NER uses the original text, not lowercased text.",
            "Stopword filtering explicitly preserves negation ('not', 'never', 'n\\'t') to prevent polarity inversion.",
            "HMM POS tagger is trained from scratch with Laplace smoothing and decoded using dynamic programming Viterbi.",
        ],
    }


def manual_vectorization(documents):
    """Teaching implementation: raw-count TF × smoothed IDF, no L2 norm."""
    counts = [Counter(re.findall(r"\b\w+\b", normalize(text))) for text in documents]
    vocabulary = sorted(set().union(*(set(row) for row in counts)))
    idf = {
        word: math.log((1 + len(documents)) / (1 + sum(word in row for row in counts))) + 1
        for word in vocabulary
    }
    return {
        "vocabulary": vocabulary,
        "bow": [[row[word] for word in vocabulary] for row in counts],
        "tfidf": [[round(row[word] * idf[word], 5) for word in vocabulary] for row in counts],
        "formula": "raw count * (log((1 + number of documents)/(1 + document frequency)) + 1); no length normalization",
    }
