import json
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.nlp import ARTIFACTS, classifier, inspect_text, linguistic_model, manual_vectorization
from backend.app.services.hosted import hosted_status, review_conversation

router = APIRouter(prefix="/api/nlp", tags=["NLP experiments"])


class InspectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class VectorizationRequest(BaseModel):
    documents: list[str] = Field(min_length=1, max_length=5)


class HostedRequest(BaseModel):
    conversation: str = Field(min_length=2, max_length=12000)
    consent_to_external_processing: Literal[True]


@lru_cache(maxsize=1)
def model_report():
    path = ARTIFACTS / "evaluation.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@router.get("/status")
def nlp_status():
    return {"classifier_loaded": classifier() is not None, "linguistic_model_loaded": linguistic_model() is not None, "local_transformer_loaded": False, "hosted": hosted_status()}


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


@router.post("/hosted-review")
def hosted_review(request: HostedRequest):
    if not hosted_status()["configured"]:
        raise HTTPException(503, "Hosted review is not configured. Set HF_TOKEN and HF_CHAT_MODEL on the backend.")
    try:
        return review_conversation(request.conversation)
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc

