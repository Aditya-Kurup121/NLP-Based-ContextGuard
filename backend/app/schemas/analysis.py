from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ContextInfo(BaseModel):
    relationship: Optional[str] = Field(default="Unspecified", description="e.g. Close friends, Classmates, Strangers, Gaming squad")
    setting: Optional[str] = Field(default="Group chat", description="e.g. Group chat, Direct message, Public forum")
    additional_information: Optional[str] = Field(default="", description="Any relevant history or context")

class AnalyzeRequest(BaseModel):
    conversation: str = Field(..., min_length=2, max_length=50000, description="Raw conversation turns in 'Speaker: Message' format")
    context: Optional[ContextInfo] = Field(default_factory=ContextInfo)

class MessageSignal(BaseModel):
    has_laughter: bool = False
    has_playful_emoji: bool = False
    has_exclusion_phrase: bool = False
    has_insult_lexicon: bool = False
    has_threat_lexicon: bool = False
    is_sarcasm_suspect: bool = False
    is_reciprocal_tease: bool = False
    is_repeated_target: bool = False
    is_victim_protest: bool = False
    is_retaliatory_threat: bool = False
    has_confrontation: bool = False
    has_intimidation: bool = False
    has_distress: bool = False
    has_bystander_defense: bool = False

class MessageAnalysis(BaseModel):
    id: int
    speaker: str
    target: Optional[str] = None
    text: str
    classification: str # Friendly Banter, Harmless / Neutral, Potentially Harmful, Possible Cyberbullying, Threat / Urgent Concern, Uncertain — More Context Needed
    confidence_score: float # 0.0 - 1.0 calibrated estimate
    confidence_category: str # Calibrated: High, Moderate, Low / Uncertain
    detected_pattern: str
    contextual_evidence: List[str]
    targeting_pattern: str
    alternative_interpretation: Optional[str] = None
    suggested_action: str
    signals: MessageSignal
    statistical_assessment: Optional[Dict[str, Any]] = None

class ParticipantInfo(BaseModel):
    name: str
    messages_sent: int
    harmful_sent: int
    targeted_count: int
    role_summary: str

class TargetingInteraction(BaseModel):
    source: str
    target: str
    harmful_turns: int
    banter_turns: int
    description: str
    is_asymmetric: bool

class ConversationMetrics(BaseModel):
    total_messages: int
    potentially_harmful_count: int
    uncertain_count: int
    friendly_banter_count: int
    neutral_count: int
    threat_count: int
    participant_count: int

class ModelInfo(BaseModel):
    engine_name: str
    engine_type: str # "Hybrid Context-Aware Rule & NLP Engine" or "Transformer Pipeline"
    execution_mode: str # "Active Local Pipeline"
    description: str
    transparency_notes: str

class AnalyzeResponse(BaseModel):
    conversation_summary: str
    overall_risk: str # Low, Moderate, High, Critical
    risk_score: float # 0 - 100 estimated risk index
    confidence: str
    metrics: ConversationMetrics
    messages: List[MessageAnalysis]
    participants: List[ParticipantInfo]
    targeting_patterns: List[TargetingInteraction]
    recommendations: List[str]
    model_info: ModelInfo
    limitations: List[str]

class ExampleConversation(BaseModel):
    id: str
    title: str
    category: str
    conversation: str
    relationship: str
    setting: str
    description: str
    expected_classification_summary: str

class ModelStatusResponse(BaseModel):
    status: str
    version: str
    engine: str
    transformer_available: bool
    features_supported: List[str]
    privacy_mode: str
