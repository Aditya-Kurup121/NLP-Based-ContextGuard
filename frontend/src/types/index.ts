export interface ContextInfo {
  relationship: string;
  setting: string;
  additional_information?: string;
}

export interface AnalyzeRequest {
  conversation: string;
  context: ContextInfo;
}

export interface MessageSignal {
  has_laughter: boolean;
  has_playful_emoji: boolean;
  has_exclusion_phrase: boolean;
  has_insult_lexicon: boolean;
  has_threat_lexicon: boolean;
  is_sarcasm_suspect: boolean;
  is_reciprocal_tease: boolean;
  is_repeated_target: boolean;
  is_victim_protest: boolean;
  is_retaliatory_threat?: boolean;
  has_confrontation?: boolean;
  has_intimidation?: boolean;
}

export interface MessageAnalysis {
  statistical_assessment?: {
    label: string;
    toxicity_score: number;
    model: string;
    top_features: Array<{ term: string; contribution: number }>;
    note: string;
  } | null;
  id: number;
  speaker: string;
  target?: string;
  text: string;
  classification: 
    | "Friendly Banter"
    | "Harmless / Neutral"
    | "Potentially Harmful"
    | "Possible Cyberbullying"
    | "Threat / Urgent Concern"
    | "Uncertain — More Context Needed";
  confidence_score: number;
  confidence_category: "High" | "Moderate" | "Low / Uncertain";
  detected_pattern: string;
  contextual_evidence: string[];
  targeting_pattern: string;
  alternative_interpretation?: string;
  suggested_action: string;
  signals: MessageSignal;
}

export interface ParticipantInfo {
  name: string;
  messages_sent: number;
  harmful_sent: number;
  targeted_count: number;
  role_summary: string;
}

export interface TargetingInteraction {
  source: string;
  target: string;
  harmful_turns: number;
  banter_turns: number;
  description: string;
  is_asymmetric: boolean;
}

export interface ConversationMetrics {
  total_messages: number;
  potentially_harmful_count: number;
  uncertain_count: number;
  friendly_banter_count: number;
  neutral_count: number;
  threat_count: number;
  participant_count: number;
}

export interface ModelInfo {
  engine_name: string;
  engine_type: string;
  execution_mode: string;
  description: string;
  transparency_notes: string;
}

export interface AnalyzeResponse {
  conversation_summary: string;
  overall_risk: "Low" | "Moderate" | "High" | "Critical";
  risk_score: number;
  confidence: string;
  metrics: ConversationMetrics;
  messages: MessageAnalysis[];
  participants: ParticipantInfo[];
  targeting_patterns: TargetingInteraction[];
  recommendations: string[];
  model_info: ModelInfo;
  limitations: string[];
}

export interface ExampleConversation {
  id: string;
  title: string;
  category: string;
  conversation: string;
  relationship: string;
  setting: string;
  description: string;
  expected_classification_summary: string;
}

export interface ModelStatusResponse {
  status: string;
  version: string;
  engine: string;
  transformer_available: boolean;
  features_supported: string[];
  privacy_mode: string;
}

export interface ClassMetric {
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface BenchmarkEvaluationResult {
  total_test_samples: number;
  overall_accuracy: number;
  macro_f1_score: number;
  per_class_metrics: Record<string, ClassMetric>;
  confusion_matrix: Record<string, Record<string, number>>;
  detailed_results: Array<{
    id: string;
    true_risk: string;
    predicted_risk: string;
    risk_score: number;
    is_correct: boolean;
    message_count: number;
    top_classification: string;
  }>;
  methodology: {
    dataset_origin: string;
    privacy_compliance: string;
    reproducibility: string;
  };
}
