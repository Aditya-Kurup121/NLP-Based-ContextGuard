const API = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api') + '/nlp';

export async function nlpRequest<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(API + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === 'string' ? error.detail : 'The NLP request could not be completed.');
  }
  return response.json();
}

export interface Inspection {
  original: string;
  noise_removed: string;
  normalized: string;
  tokenization: {
    sentences?: string[];
    word_and_punctuation: string[];
    characters: string[];
    wordpiece?: string[] | null;
    bpe?: string[] | null;
  };
  tokens: Array<{
    text: string;
    lemma: string;
    pos: string;
    tag?: string;
    dependency: string;
    head: string;
    start: number;
    end: number;
  }>;
  entities: Array<{ text: string; label: string; start: number; end: number }>;
  noun_chunks: Array<{ text: string; root: string }>;
  stemming: { porter: string[]; lancaster: string[] };
  stopword_analysis?: {
    filtered_text: string;
    removed_stopwords: string[];
    preserved_negations: string[];
  };
  stopword_filtered: string[];
  vocabulary: {
    original: number;
    noise_cleaned?: number;
    porter: number;
    lancaster?: number;
    lemmatized: number | null;
  };
  ngrams: Record<string, string[]>;
  regex_entities?: {
    urls: string[];
    emails: string[];
    mentions: string[];
    dates: string[];
  };
  hmm_pos_tagging?: {
    tags: string[];
    log_likelihood: number;
    model_type: string;
    pos_comparison: Array<{
      token: string;
      spacy_pos: string;
      hmm_pos: string;
      match: boolean;
    }>;
  };
  linguistic_model: string | null;
  linguistic_status: string;
}

export interface LevenshteinResult {
  str1: string;
  str2: string;
  distance: number;
  similarity_ratio: number;
  matrix: number[][];
  operations: Array<{
    op: 'match' | 'insert' | 'delete' | 'substitute';
    char1: string;
    char2: string;
    cost: number;
  }>;
  header_x: string[];
  header_y: string[];
}

export interface Word2VecStatus {
  vocabulary_size: number;
  embedding_dim: number;
  window_size: number;
  trained_epochs: number;
  corpus_sentences: number;
  sample_words: string[];
  method: string;
  default_corpus_sample?: string[];
}

export interface WordNeighbor {
  word: string;
  similarity: number;
}

export interface WordAnalogyResult {
  analogy: string;
  results: WordNeighbor[];
}

export interface HmmTagResult {
  tokens: string[];
  hmm_tags: string[];
  viterbi_log_likelihood: number;
  comparison: Array<{
    token: string;
    hmm_pos: string;
    spacy_pos: string;
    match: boolean;
  }>;
}

interface Score {
  accuracy: number;
  macro_f1: number;
  confusion_matrix: number[][];
  per_class: Record<string, { precision: number; recall: number; 'f1-score': number; support: number }>;
}

export interface ModelReport {
  dataset: string;
  source_url: string;
  dataset_revision: string;
  task: string;
  split_sizes: Record<string, number>;
  selected_model: string;
  models: Record<string, { validation: Score; test: Score }>;
  majority_baseline: Score;
  limitations: string[];
  exact_cross_split_duplicates_removed: number;
}

export interface HostedStatus {
  configured: boolean;
  provider: string;
  model: string | null;
}

export interface HostedReview {
  risk: string;
  summary: string;
  evidence: Array<{ quote: string; explanation: string }>;
  alternative_interpretation: string;
  suggested_action: string;
  provider: string;
  model: string;
  note: string;
}
