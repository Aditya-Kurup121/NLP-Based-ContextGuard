"""Inspectable linguistic analysis and a locally trained statistical classifier."""
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"


def normalize(text):
    # Preserve emojis, punctuation and negation. Replace identifiers with markers.
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
def subword_tokenizer(name):
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


def inspect_text(text):
    from nltk.stem import PorterStemmer, LancasterStemmer
    nlp = linguistic_model()
    normalized = normalize(text)
    words = re.findall(r"\w+(?:['’]\w+)*|[^\w\s]", normalized)
    porter, lancaster = PorterStemmer(), LancasterStemmer()
    entities, tokens, chunks = [], [], []
    if nlp:
        doc = nlp(text)  # Original case and punctuation are essential for NER.
        tokens = [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_, "tag": t.tag_, "dependency": t.dep_, "head": t.head.text, "is_stop": bool(t.is_stop), "start": t.idx, "end": t.idx + len(t)} for t in doc if not t.is_space]
        entities = [{"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char} for ent in doc.ents]
        chunks = [{"text": chunk.text, "root": chunk.root.text} for chunk in doc.noun_chunks]
    # Do not remove negation even when it appears in spaCy's stopword list.
    negation = {"not", "no", "never", "n't", "n’t", "cannot"}
    filtered = [t["text"] for t in tokens if not t["is_stop"] or t["text"].lower() in negation] if tokens else words
    return {
        "original": text, "normalized": normalized,
        "tokenization": {"word_and_punctuation": words, "characters": list(text), **{name: tokenizer.encode(text).tokens if (tokenizer := subword_tokenizer(name)) else None for name in ("wordpiece", "bpe")}},
        "tokens": tokens, "entities": entities, "noun_chunks": chunks,
        "stemming": {"porter": [porter.stem(w) for w in words], "lancaster": [lancaster.stem(w) for w in words]},
        "stopword_filtered": filtered,
        "vocabulary": {"original": len(set(words)), "porter": len({porter.stem(w) for w in words}), "lemmatized": len({t["lemma"] for t in tokens}) if tokens else None},
        "ngrams": {str(n): [" ".join(words[i:i+n]) for i in range(max(0, len(words)-n+1))][:100] for n in (1, 2, 3)},
        "regex_entities": {"urls": re.findall(r"https?://\S+", text), "emails": re.findall(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", text), "mentions": re.findall(r"(?<!\w)@[\w]+", text), "dates": re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)},
        "linguistic_model": "en_core_web_sm" if nlp else None,
        "linguistic_status": "loaded" if nlp else "Install the en_core_web_sm model for POS, lemmas and NER.",
        "classifier": classify_texts([text])[0],
        "notes": ["NER uses the original text, not the lowercased text.", "Stopword filtering and stemming are demonstrations; the trained classifier preserves negation and uses its own fitted vectorizer."],
    }


def manual_vectorization(documents):
    """Small teaching implementation: raw-count TF × smoothed IDF, no L2 norm."""
    counts = [Counter(re.findall(r"\b\w+\b", normalize(text))) for text in documents]
    vocabulary = sorted(set().union(*(set(row) for row in counts)))
    idf = {word: math.log((1 + len(documents)) / (1 + sum(word in row for row in counts))) + 1 for word in vocabulary}
    return {"vocabulary": vocabulary, "bow": [[row[word] for word in vocabulary] for row in counts], "tfidf": [[round(row[word] * idf[word], 5) for word in vocabulary] for row in counts], "formula": "raw count * (log((1 + number of documents)/(1 + document frequency)) + 1); no length normalization"}
