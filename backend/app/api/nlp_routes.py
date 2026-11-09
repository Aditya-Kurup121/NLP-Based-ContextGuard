import json
import re
from functools import lru_cache
from typing import Literal, Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.nlp import (
    ARTIFACTS,
    classifier,
    inspect_text,
    linguistic_model,
    manual_vectorization,
)
from backend.app.services.hosted import hosted_status, review_conversation
from backend.app.services.transformer import context_model_status, transformer_status
from backend.app.services.levenshtein import compute_levenshtein
from backend.app.services.word2vec import (
    get_word2vec_model,
    train_custom_word2vec_model,
    DEFAULT_CORPUS,
)
from backend.app.services.hmm_tagger import get_hmm_tagger

router = APIRouter(prefix="/api/nlp", tags=["NLP experiments"])


class InspectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class VectorizationRequest(BaseModel):
    documents: list[str] = Field(min_length=1, max_length=5)


class HostedRequest(BaseModel):
    conversation: str = Field(min_length=2, max_length=12000)
    consent_to_external_processing: Literal[True]


class LevenshteinRequest(BaseModel):
    str1: str = Field(default="cyberbullying", max_length=100)
    str2: str = Field(default="cyberbully", max_length=100)


class Word2VecVectorRequest(BaseModel):
    word: str = Field(min_length=1, max_length=50)
    model_id: Optional[str] = Field(default=None, max_length=64)


class Word2VecSimilarityRequest(BaseModel):
    word1: str = Field(min_length=1, max_length=50)
    word2: str = Field(min_length=1, max_length=50)
    model_id: Optional[str] = Field(default=None, max_length=64)


class Word2VecSimilarRequest(BaseModel):
    word: str = Field(min_length=1, max_length=50)
    top_n: int = Field(default=6, ge=1, le=20)
    model_id: Optional[str] = Field(default=None, max_length=64)


class Word2VecAnalogyRequest(BaseModel):
    a: str = Field(min_length=1, max_length=50)
    b: str = Field(min_length=1, max_length=50)
    c: str = Field(min_length=1, max_length=50)
    model_id: Optional[str] = Field(default=None, max_length=64)


class Word2VecTrainRequest(BaseModel):
    corpus: list[str] = Field(min_length=2, max_length=100)
    epochs: int = Field(default=35, ge=5, le=100)


class HmmTagRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def resolve_w2v(model_id: Optional[str]):
    try:
        return get_word2vec_model(model_id)
    except KeyError:
        raise HTTPException(404, "Custom Word2Vec model not found (it may have expired). Retrain it or use the default model.")


@lru_cache(maxsize=1)
def model_report():
    path = ARTIFACTS / "evaluation.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@router.get("/status")
def nlp_status():
    w2v = get_word2vec_model()
    return {
        "classifier_loaded": classifier() is not None,
        "linguistic_model_loaded": linguistic_model() is not None,
        "local_transformer_loaded": transformer_status()["loaded"],
        "transformer": transformer_status(),
        "context_model": context_model_status(),
        "word2vec_loaded": len(w2v.vocab) > 0,
        "hmm_tagger_loaded": True,
        "hosted": hosted_status(),
    }


@router.post("/inspect")
def inspect(request: InspectRequest):
    if not request.text.strip():
        raise HTTPException(400, "Enter some text to inspect.")
    return inspect_text(request.text)


@router.post("/vectorize")
def vectorize(request: VectorizationRequest):
    if any(not text.strip() or len(text) > 500 for text in request.documents):
        raise HTTPException(400, "Provide 1–5 non-empty documents of at most 500 characters each.")
    return manual_vectorization(request.documents)


@router.get("/evaluation")
def evaluation():
    report = model_report()
    if report is None:
        raise HTTPException(503, "Train the classifiers with python -m backend.training.train first.")
    return report


@router.post("/levenshtein")
def levenshtein_distance(request: LevenshteinRequest):
    return compute_levenshtein(request.str1, request.str2)


@router.get("/word2vec/status")
def word2vec_status():
    w2v = get_word2vec_model()
    return {
        **w2v.get_summary(),
        "default_corpus_sample": DEFAULT_CORPUS[:5],
    }


@router.post("/word2vec/vector")
def word2vec_vector(request: Word2VecVectorRequest):
    w2v = resolve_w2v(request.model_id)
    vector = w2v.get_vector(request.word)
    if vector is None:
        raise HTTPException(404, f"Word '{request.word}' is out of vocabulary.")
    return {
        "word": request.word.lower().strip(),
        "dimensions": len(vector),
        "vector": [round(x, 4) for x in vector],
    }


@router.post("/word2vec/similarity")
def word2vec_similarity(request: Word2VecSimilarityRequest):
    w2v = resolve_w2v(request.model_id)
    sim = w2v.cosine_similarity(request.word1, request.word2)
    if sim is None:
        missing = []
        if request.word1.lower().strip() not in w2v.vocab:
            missing.append(request.word1)
        if request.word2.lower().strip() not in w2v.vocab:
            missing.append(request.word2)
        raise HTTPException(404, f"Out of vocabulary word(s): {', '.join(missing)}")
    return {
        "word1": request.word1.lower().strip(),
        "word2": request.word2.lower().strip(),
        "cosine_similarity": sim,
        "interpretation": "High semantic similarity" if sim > 0.5 else "Moderate similarity" if sim > 0.1 else "Low / Orthogonal similarity",
    }


@router.post("/word2vec/similar")
def word2vec_similar(request: Word2VecSimilarRequest):
    w2v = resolve_w2v(request.model_id)
    if request.word.lower().strip() not in w2v.vocab:
        raise HTTPException(404, f"Word '{request.word}' is out of vocabulary. Try: {', '.join(w2v.inv_vocab[:10])}")
    neighbors = w2v.nearest_neighbors(request.word, top_n=request.top_n)
    return {
        "query": request.word.lower().strip(),
        "nearest_neighbors": neighbors,
    }


@router.post("/word2vec/analogy")
def word2vec_analogy(request: Word2VecAnalogyRequest):
    w2v = resolve_w2v(request.model_id)
    for w in (request.a, request.b, request.c):
        if w.lower().strip() not in w2v.vocab:
            raise HTTPException(404, f"Word '{w}' is out of vocabulary.")
    results = w2v.analogy(request.a, request.b, request.c)
    return {
        "analogy": f"{request.a} : {request.b} :: {request.c} : ?",
        "results": results,
    }


@router.post("/word2vec/train")
def word2vec_train(request: Word2VecTrainRequest):
    try:
        model_id, model = train_custom_word2vec_model(request.corpus, epochs=request.epochs)
        return {
            "status": "trained",
            "model_id": model_id,
            **model.get_summary(),
        }
    except Exception as exc:
        raise HTTPException(400, f"Training failed: {str(exc)}") from exc


@router.post("/hmm/tag")
def hmm_pos_tag(request: HmmTagRequest):
    text = request.text.strip()
    matches = list(re.finditer(r"\w+(?:['’]\w+)*|[^\w\s]", text))
    tokens = [m.group() for m in matches]
    if not tokens:
        raise HTTPException(400, "Provide valid text to tag.")
    hmm = get_hmm_tagger()
    tags, score, _ = hmm.viterbi(tokens)
    nlp = linguistic_model()
    spacy_tags = []
    if nlp:
        # Align by character position, not token text, so repeated words
        # ("I said I would") each get their own spaCy tag.
        doc = nlp(text)
        for m in matches:
            span = doc.char_span(m.start(), m.end(), alignment_mode="expand")
            spacy_tags.append(span[0].pos_ if span is not None and len(span) else "X")

    comparison = []
    for i, tok in enumerate(tokens):
        st = spacy_tags[i] if i < len(spacy_tags) else "X"
        ht = tags[i]
        comparison.append({
            "token": tok,
            "hmm_pos": ht,
            "spacy_pos": st,
            "match": (ht == st),
        })

    return {
        "tokens": tokens,
        "hmm_tags": tags,
        "viterbi_log_likelihood": score,
        "comparison": comparison,
    }


@router.post("/hosted-review")
def hosted_review(request: HostedRequest):
    if not hosted_status()["configured"]:
        raise HTTPException(503, "Hosted review is not configured. Set HF_TOKEN and HF_CHAT_MODEL on the backend.")
    try:
        return review_conversation(request.conversation)
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
