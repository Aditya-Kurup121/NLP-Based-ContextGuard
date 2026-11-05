from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.whatsapp import analyze_export, parse_export

router = APIRouter(prefix="/api/imports/whatsapp", tags=["WhatsApp imports"])


class ImportRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2 * 1024 * 1024)
    date_order: Literal["DMY", "MDY"] = "DMY"
    anonymize: bool = False
    relationship: str = Field(default="Unspecified", max_length=100)


@router.post("/preview")
def preview(request: ImportRequest):
    try:
        return parse_export(request.text, request.date_order, request.anonymize)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/analyze")
def analyze(request: ImportRequest):
    try:
        parsed = parse_export(request.text, request.date_order, request.anonymize)
        return analyze_export(parsed, request.relationship)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
