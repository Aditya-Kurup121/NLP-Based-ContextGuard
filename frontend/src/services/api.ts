import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ExampleConversation,
  ModelStatusResponse,
  BenchmarkEvaluationResult
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

export async function checkBackendHealth(): Promise<ModelStatusResponse> {
  const res = await fetch(`${API_BASE}/health`, {
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchExamples(): Promise<ExampleConversation[]> {
  const res = await fetch(`${API_BASE}/examples`, {
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    throw new Error(`Failed to load examples: ${res.statusText}`);
  }
  return res.json();
}

export async function analyzeConversation(data: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Analysis request failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchModelInfo(): Promise<any> {
  const res = await fetch(`${API_BASE}/model-info`, {
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch model info: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchEvaluationBenchmark(): Promise<BenchmarkEvaluationResult> {
  const res = await fetch(`${API_BASE}/evaluate`, {
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    throw new Error(`Failed to run benchmark evaluation: ${res.statusText}`);
  }
  return res.json();
}
