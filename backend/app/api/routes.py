from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from backend.app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExampleConversation,
    ModelStatusResponse,
    ModelInfo
)
from backend.app.services.engine import ContextGuardAnalysisEngine
from backend.app.services.examples import get_examples, get_example_by_id
from backend.app.services.evaluator import run_benchmark_evaluation

router = APIRouter(prefix="/api", tags=["ContextGuard API"])
engine = ContextGuardAnalysisEngine()

@router.get("/health", response_model=ModelStatusResponse)
def health_check():
    """Returns backend health, active NLP pipeline status, and privacy configuration."""
    return ModelStatusResponse(
        status="healthy",
        version=engine.version,
        engine=engine.engine_name,
        transformer_available=engine.transformer_available,
        features_supported=[
            "multi_turn_dialogue_parsing",
            "reciprocal_banter_detection",
            "repeated_targeting_asymmetry",
            "sarcasm_inversion_heuristics",
            "calibrated_explainability",
            "zero_cloud_leak_privacy"
        ],
        privacy_mode="Strict Local Processing (Zero Persistent Conversation Logging)"
    )

@router.get("/examples", response_model=List[ExampleConversation])
def list_examples():
    """Retrieves preloaded demonstration conversations with expected behavior summaries."""
    return get_examples()

@router.get("/examples/{example_id}", response_model=ExampleConversation)
def get_single_example(example_id: str):
    """Retrieves a single demonstration conversation by ID."""
    return get_example_by_id(example_id)

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_conversation(request: AnalyzeRequest):
    """
    Analyzes an entire conversation context-awares.
    Computes message classifications, risk level, targeting patterns, and plain-English explainability.
    """
    if not request.conversation or not request.conversation.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation text cannot be empty. Please provide dialogue turns."
        )

    if len(request.conversation) > 50000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Conversation exceeds 50,000 characters limit."
        )

    try:
        response = engine.analyze(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(e)}"
        )

@router.get("/model-info")
def get_model_info():
    """Returns the analysis engine architecture, execution mode, and research limitations."""
    return {
        "engine_name": engine.engine_name,
        "engine_type": "Hybrid Multi-Turn Dialogue Rule & Calibrated Context Engine",
        "transformer_installed": engine.transformer_available,
        "execution_mode": "Active Local Pipeline",
        "features": [
            "Dialogue Turn Parsing & Sequence Tracking",
            "Reciprocal Banter Recognition via Emoji & Laughter Anchors",
            "Sarcasm & Tone Shift Identification",
            "Targeting Asymmetry Matrix (Who targets whom)",
            "Systematic Exclusion vs Isolated Irritation Distinction",
            "Calibrated Uncertainty & Explainable Evidence"
        ],
        "licensing": "MIT License - Open Academic & Assistive Research",
        "privacy_notice": "Conversations are analyzed in memory and immediately discarded. No messages are stored or transmitted externally.",
        "limitations": [
            "Assists human decision-makers; does not provide legal or definitive psychological diagnoses.",
            "Text alone lacks vocal pitch, body language, and historical unrecorded friendships.",
            "Regional vernacular and in-group irony may cause calibration variance."
        ]
    }

@router.get("/evaluate")
def get_evaluation_metrics():
    """Runs automated evaluation on benchmark dataset and returns confusion matrix and F1 scores."""
    return run_benchmark_evaluation()
