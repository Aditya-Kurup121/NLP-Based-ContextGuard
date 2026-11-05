import type { MessageAnalysis } from '../types';

export interface ImportedMessage {
  id: number;
  speaker: string | null;
  text: string;
  timestamp: string | null;
  timestamp_raw: string;
  line_start: number;
  line_end: number;
  kind: 'text' | 'system' | 'media' | 'empty' | 'unparsed';
}
export interface ImportPreview {
  messages: ImportedMessage[];
  participants: string[];
  counts: Record<string, number>;
  total_entries: number;
  date_order: 'DMY' | 'MDY';
  date_start: string | null;
  date_end: string | null;
  warnings: Array<{ line: number; reason: string; excerpt: string }>;
  warning_count: number;
  notices: string[];
  anonymized: boolean;
  source_sha256: string;
}
interface DiscussionSummary {
  keywords: string[];
  excerpts: Array<{ message_id: number; speaker: string; timestamp_raw: string; text: string; excerpt_truncated: boolean }>;
  method: string;
}
export interface ImportReport {
  created_at: string;
  import: ImportPreview;
  overview: {
    text_message_count: number;
    excluded_entries: number;
    participant_count: number;
    participants: Array<{ name: string; message_count: number; flagged_count: number }>;
    summary: DiscussionSummary;
    narrative: string;
  };
  risk: {
    level: string;
    index: number;
    flagged_count: number;
    threat_count: number;
    uncertain_count: number;
    window_count: number;
    peak_window: { first_message_id: number; last_message_id: number; score: number; summary: string };
    method: string;
  };
  chapters: Array<{ id: number; first_message_id: number; last_message_id: number; start: string; end: string; message_count: number; flagged_count: number; summary: DiscussionSummary }>;
  episodes: Array<{ id: number; first_message_id: number; last_message_id: number; flagged_message_ids: number[]; has_threat: boolean; messages: Array<ImportedMessage & { analysis: MessageAnalysis | null }> }>;
  analysis: MessageAnalysis[];
  limitations: string[];
  exports: { markdown: string; html: string };
}
export interface ImportOptions {
  text: string;
  date_order: 'DMY' | 'MDY';
  anonymize: boolean;
  relationship: string;
}
const API = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api') + '/imports/whatsapp';

export async function importRequest<T>(action: 'preview' | 'analyze', options: ImportOptions): Promise<T> {
  const response = await fetch(`${API}/${action}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(options),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === 'string' ? error.detail : 'The import could not be completed. Check the file size and format.');
  }
  return response.json();
}

export function downloadReport(report: ImportReport, kind: 'html' | 'markdown') {
  const blob = new Blob([report.exports[kind]], { type: kind === 'html' ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `contextguard-report.${kind === 'html' ? 'html' : 'md'}`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const SAMPLE_EXPORT = `28/10/2026, 09:00 - Messages and calls are end-to-end encrypted.
28/10/2026, 09:01 - Maya: Can we meet at 4 to finish the NLP project slides?
28/10/2026, 09:02 - Jordan: Yes. I will prepare the dataset evaluation table.
28/10/2026, 09:03 - Sam: I can explain TF-IDF and the confusion matrix.
28/10/2026, 09:04 - Maya: Great, please include the limitations too.
28/10/2026, 09:05 - Jordan: <Media omitted>
28/10/2026, 16:00 - Maya: Has everyone added their project slides?
28/10/2026, 16:01 - Jordan: you motherfucking moron
28/10/2026, 16:02 - Maya: Please stop making personal comments.
28/10/2026, 16:03 - Jordan: ill kill you
28/10/2026, 16:04 - Sam: Jordan, cut it out. This is unnecessary.
28/10/2026, 16:05 - Maya: I am leaving this discussion for now.
29/10/2026, 10:00 - Sam: I have shared the final project slides with our teacher.
29/10/2026, 10:01 - Maya: Thank you. We should explain the evaluation results clearly.`;
