import { useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { ArrowDownToLine, ArrowRight, FileText, Upload, X, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { importRequest, downloadReport, SAMPLE_EXPORT } from '../services/imports';
import type { ImportOptions, ImportPreview, ImportReport, ImportedMessage } from '../services/imports';
import { MessageDetailModal } from './MessageDetailModal';
import type { MessageAnalysis } from '../types';
import './WhatsAppImport.css';

const PAGE_SIZE = 40;
const concernLabels = new Set(['Potentially Harmful', 'Possible Cyberbullying', 'Threat / Urgent Concern']);

export function WhatsAppImport() {
  const [text, setText] = useState('');
  const [filename, setFilename] = useState('');
  const [dateOrder, setDateOrder] = useState<'DMY' | 'MDY'>('DMY');
  const [anonymize, setAnonymize] = useState(true);
  const [relationship, setRelationship] = useState('Unspecified');
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [stage, setStage] = useState<'idle' | 'reading' | 'previewing' | 'analyzing'>('idle');
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [speaker, setSpeaker] = useState('all');
  const [filter, setFilter] = useState<'all' | 'concern' | 'excluded'>('all');
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<MessageAnalysis | null>(null);
  const [focusId, setFocusId] = useState<number | null>(null);
  const requestVersion = useRef(0);
  const fileInput = useRef<HTMLInputElement>(null);
  const transcript = useRef<HTMLDivElement>(null);
  const riskCard = useRef<HTMLElement>(null);
  const busy = stage !== 'idle';
  const options: ImportOptions = { text, date_order: dateOrder, anonymize, relationship };
  const analysisById = new Map(report?.analysis.map(message => [message.id, message]) || []);
  const visible = (preview?.messages || []).filter(message => {
    const assessment = analysisById.get(message.id);
    return (speaker === 'all' || message.speaker === speaker)
      && (filter === 'all' || (filter === 'excluded' ? message.kind !== 'text' : assessment && concernLabels.has(assessment.classification)))
      && (!query || `${message.speaker || ''} ${message.text}`.toLowerCase().includes(query.toLowerCase()));
  });
  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);

  function invalidate() {
    requestVersion.current += 1;
    setPreview(null); setReport(null); setError(''); setQuery(''); setSpeaker('all'); setFilter('all'); setPage(0); setSelected(null); setFocusId(null);
  }
  async function loadFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    invalidate(); setText(''); setFilename('');
    if (!file.name.toLowerCase().endsWith('.txt')) { setError('Choose the .txt file exported by WhatsApp without media. ZIP files, backups, PDFs, and images are not supported in this version.'); return; }
    if (file.size === 0) { setError('The export is empty. Choose a WhatsApp .txt export containing messages.'); return; }
    if (file.size > 2 * 1024 * 1024) { setError('This version supports text exports up to 2 MiB and 5,000 entries. Split a larger export before importing.'); return; }
    const version = requestVersion.current;
    setStage('reading');
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      const encoding = bytes[0] === 0xff && bytes[1] === 0xfe ? 'utf-16le' : bytes[0] === 0xfe && bytes[1] === 0xff ? 'utf-16be' : 'utf-8';
      const decoded = new TextDecoder(encoding, { fatal: true }).decode(bytes);
      if (!decoded.trim()) { if (version === requestVersion.current) setError('The export is empty. Choose a WhatsApp .txt export containing messages.'); return; }
      if (version === requestVersion.current) { setText(decoded); setFilename(file.name); }
    } catch { if (version === requestVersion.current) setError('This file could not be decoded. Select an uncorrupted UTF-8 or UTF-16 text export.'); }
    finally { if (version === requestVersion.current) setStage('idle'); }
  }
  async function parse() {
    const version = requestVersion.current;
    setStage('previewing'); setError('');
    try { const result = await importRequest<ImportPreview>('preview', options); if (version === requestVersion.current) { setPreview(result); setReport(null); setPage(0); } }
    catch (e) { if (version === requestVersion.current) setError(e instanceof Error ? e.message : 'Import failed.'); }
    finally { if (version === requestVersion.current) setStage('idle'); }
  }
  async function analyze() {
    const version = requestVersion.current;
    setStage('analyzing'); setError('');
    try { const result = await importRequest<ImportReport>('analyze', options); if (version === requestVersion.current) { setReport(result); setPreview(result.import); setTimeout(() => riskCard.current?.scrollIntoView({ block: 'start', behavior: 'smooth' }), 0); } }
    catch (e) { if (version === requestVersion.current) setError(e instanceof Error ? e.message : 'Analysis failed.'); }
    finally { if (version === requestVersion.current) setStage('idle'); }
  }
  function jumpToMessage(id: number) {
    setQuery(''); setSpeaker('all'); setFilter('all'); setPage(Math.floor((id - 1) / PAGE_SIZE)); setFocusId(id);
    setTimeout(() => {
      const target = document.getElementById(`transcript-message-${id}`);
      (target || transcript.current)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      target?.focus({ preventScroll: true });
    }, 0);
  }
  function renderMessage(message: ImportedMessage, scope: string) {
    const assessment = analysisById.get(message.id);
    const flagged = assessment && concernLabels.has(assessment.classification);
    return <article key={message.id} id={`${scope}-message-${message.id}`} tabIndex={-1} className={`import-message ${flagged ? 'flagged' : ''} ${focusId === message.id ? 'focused-message' : ''}`}>
      <div className="import-message-meta"><strong>{message.speaker || 'System / unparsed'}</strong><time>{message.timestamp_raw || 'No timestamp'}</time><button onClick={() => setFocusId(message.id)} aria-label={`Mark message ${message.id}`}>#{message.id}</button></div>
      <p>{message.text || '(empty message)'}</p>
      <div className="import-message-bottom"><span>Source lines {message.line_start}–{message.line_end}{message.kind !== 'text' && ` · ${message.kind} · excluded from analysis`}</span>{assessment && <button className={flagged ? 'flag-label' : ''} onClick={() => setSelected(assessment)}>{assessment.classification} <ArrowRight size={12} /></button>}</div>
    </article>;
  }
  return <section className="whatsapp-workspace" aria-busy={busy}>
    <div className="import-hero"><div><p className="eyebrow">FROM CHAT HISTORY TO A CLEARER PICTURE</p><h1>A conversation, in context.</h1><p>Import a WhatsApp text export. Explore what was discussed, review the evidence, and take away a readable report.</p></div><FileText size={42} strokeWidth={1} /></div>
    <div className="import-steps" aria-label="Import progress"><span className={text ? 'complete' : 'current'}>01 <strong>Choose export</strong></span><span className={preview ? 'complete' : text ? 'current' : ''}>02 <strong>Check parsing</strong></span><span className={report ? 'complete' : preview ? 'current' : ''}>03 <strong>Review & report</strong></span></div>
    <section className="lab-panel import-upload"><div><p className="eyebrow">YOUR EXPORT / YOUR CONTROL</p><h2>Start with the text file.</h2><p>In WhatsApp, choose Export chat → Without media, then select the exported .txt file here. Text is processed by your configured local backend; this workflow does not call an external model.</p><p className="lab-note">Up to 2 MiB · 5,000 entries · 100 participants · Android and iPhone timestamp styles · UTF-8 / UTF-16</p></div>
      <div className="import-file-actions"><input ref={fileInput} tabIndex={-1} type="file" accept=".txt,text/plain" aria-label="Choose WhatsApp text export" disabled={busy} onChange={loadFile} /><button className="primary-action" onClick={() => fileInput.current?.click()} disabled={busy}><Upload size={16} />{text ? 'Choose another export' : 'Choose .txt export'}</button><button className="clear-action" disabled={busy} onClick={() => { invalidate(); setFilename('Example project chat.txt'); setText(SAMPLE_EXPORT); }}>Try a synthetic sample <ArrowRight size={14} /></button></div>
      {filename && <div className="chosen-file"><FileText size={16} /><span>{filename}</span><small>{new Blob([text]).size.toLocaleString()} decoded bytes</small><button aria-label="Remove imported file and clear report" disabled={busy} onClick={() => { invalidate(); setText(''); setFilename(''); }}><X size={15} /></button></div>}
      {text && <><div className="import-options"><label>Date order<select disabled={busy} value={dateOrder} onChange={e => { invalidate(); setDateOrder(e.target.value as 'DMY' | 'MDY'); }}><option value="DMY">Day / Month / Year</option><option value="MDY">Month / Day / Year</option></select></label><label>Relationship<select value={relationship} disabled={busy} onChange={e => { invalidate(); setRelationship(e.target.value); }}><option>Unspecified</option><option>Classmates</option><option>Close friends</option><option>Coworkers</option><option>Strangers</option></select></label><label className="import-anonymize"><input type="checkbox" checked={anonymize} disabled={busy} onChange={e => { invalidate(); setAnonymize(e.target.checked); }} /><span>Mask participant names, emails & phone numbers<small>Applied to the preview, analysis and downloaded report. Other identifying details may remain.</small></span></label></div><button className="primary-action" disabled={busy} onClick={parse}>{stage === 'reading' ? 'Reading export…' : stage === 'previewing' ? 'Checking format…' : preview ? 'Refresh parsing preview' : 'Check parsing & preview'}<ArrowRight size={16} /></button></>}
    </section>
    {error && <p className="editor-error" role="alert">{error}</p>}
    {preview && <>
      <section className="lab-panel import-quality"><div className="import-section-heading"><div><p className="eyebrow">02 / CHECK BEFORE YOU ANALYZE</p><h2>{preview.total_entries.toLocaleString()} entries, accounted for.</h2></div>{!report && <button className="primary-action" onClick={analyze} disabled={busy || !(preview.counts.text > 0)}>{stage === 'analyzing' ? 'Analyzing all text messages…' : 'Analyze & draft report'}<ArrowRight size={16} /></button>}</div>
        <div className="import-counts"><div><strong>{preview.counts.text || 0}</strong><span>Text messages</span></div><div><strong>{preview.participants.length}</strong><span>Participants</span></div><div><strong>{preview.counts.system || 0}</strong><span>System events</span></div><div><strong>{preview.counts.media || 0}</strong><span>Attachment-only</span></div><div><strong>{preview.warning_count}</strong><span>Parsing warnings</span></div></div>
        <p className="lab-note">{preview.date_start?.replace('T', ' ') || 'Unknown start'} → {preview.date_end?.replace('T', ' ') || 'Unknown end'} · export local time</p>{preview.notices.map(notice => <p className="lab-note" key={notice}>{notice}</p>)}
        {(preview.warning_count > 0 || preview.counts.unparsed || preview.counts.empty) && <details className="parse-warnings"><summary>Review parsing warnings and excluded entries</summary><p>{preview.counts.unparsed || 0} malformed entries; {preview.counts.empty || 0} empty entries. Warnings can affect coverage. Only the first 100 warnings are listed.</p>{preview.warnings.map((warning, i) => <p key={i}><strong>Line {warning.line}:</strong> {warning.reason} <code>{warning.excerpt}</code></p>)}</details>}
        {stage === 'analyzing' && <p role="status" className="lab-note">Reviewing overlapping conversation windows and extracting discussion sessions. Longer files can take a little time; no text is being sent to a hosted model.</p>}
      </section>
      {report && <>
        <section ref={riskCard} aria-label="Imported conversation risk" className={`import-risk ${report.risk.level.toLowerCase()}`}><div><p className="eyebrow">03 / THE REVIEW</p><h2>{report.risk.level} concern</h2><p>{report.risk.flagged_count} messages flagged for review · {report.risk.threat_count} threat cues · {report.risk.uncertain_count} uncertain</p></div><div className="import-risk-number"><strong>{report.risk.index.toFixed(0)}</strong><span>/ 100</span><small>Heuristic index, not a probability</small></div></section>
        <section className="lab-panel"><p className="eyebrow">WHAT WAS DISCUSSED</p><h2>The conversation at a glance.</h2><p>{report.overview.narrative}</p><div className="feature-chips">{report.overview.summary.keywords.map(word => <span className="away-toxic" key={word}>{word}</span>)}</div><p className="lab-note">{report.overview.summary.method}. Quotations below can be opened in the transcript.</p><div className="source-excerpts">{report.overview.summary.excerpts.map(excerpt => <button key={excerpt.message_id} onClick={() => jumpToMessage(excerpt.message_id)}><span>#{excerpt.message_id} · {excerpt.speaker} · {excerpt.timestamp_raw}</span><p>“{excerpt.text}{excerpt.excerpt_truncated ? '…' : ''}”</p><small>Open source message <ArrowRight size={12} /></small></button>)}</div></section>
        <section className="lab-panel"><div className="import-section-heading"><div><p className="eyebrow">DISCUSSION CHAPTERS</p><h2>Follow the sessions.</h2></div><span className="lab-note">{report.chapters.length} sessions</span></div><p className="lab-note">Split at date changes, gaps of 60 minutes, or 100 text messages. These are time-based sessions, not learned topic boundaries.</p><div className="discussion-chapters">{report.chapters.map(chapter => <button key={chapter.id} onClick={() => jumpToMessage(chapter.first_message_id)}><span className="chapter-number">{String(chapter.id).padStart(2, '0')}</span><div><strong>{chapter.summary.keywords.slice(0, 3).join(' · ') || 'General discussion'}</strong><p>{chapter.start} → {chapter.end}</p><small>{chapter.message_count} messages · {chapter.flagged_count} flagged</small></div><ArrowRight size={16} /></button>)}</div></section>
        <section className="lab-panel"><p className="eyebrow">EVIDENCE / WITH SURROUNDING REPLIES</p><h2>Where a closer look is needed.</h2>{!report.episodes.length && <p>No messages matched the current concern categories. This does not establish that the conversation is safe.</p>}{report.episodes.map(episode => <details key={episode.id} className="evidence-episode"><summary><span>{episode.has_threat ? 'Threat cues' : 'Concerning exchange'} · messages #{episode.first_message_id}–#{episode.last_message_id}</span><small>{episode.flagged_message_ids.length} flagged</small></summary><div>{episode.messages.map(message => renderMessage(message, `episode-${episode.id}`))}</div></details>)}</section>
        <section className="lab-panel"><p className="eyebrow">HOW THE INDEX WAS CALCULATED</p><h2>The incident matters, even in a long chat.</h2><p>{report.risk.method}</p><p className="lab-note">{report.risk.window_count} windows reviewed · {report.overview.text_message_count} unique text messages · {report.overview.excluded_entries} excluded entries</p><button className="source-link" onClick={() => jumpToMessage(report.risk.peak_window.first_message_id)}>Inspect highest-concern window: #{report.risk.peak_window.first_message_id}–#{report.risk.peak_window.last_message_id}<ArrowRight size={14} /></button><p className="lab-note">{report.risk.peak_window.summary}</p><h3>Participant activity</h3><div className="participant-activity">{report.overview.participants.map(person => <div key={person.name}><strong>{person.name}</strong><span>{person.message_count} messages</span><span>{person.flagged_count} flagged</span></div>)}</div><p className="lab-note">Activity counts describe messages, not guilt or intent. Inferred recipients can be wrong in a group chat.</p></section>
        <section className="report-download lab-panel"><div><p className="eyebrow">TAKE THE EVIDENCE WITH YOU</p><h2>Your conversation report.</h2><p>Includes the overview, discussion sessions, risk method, evidence, source references, and limitations. Participant masking is {report.import.anonymized ? 'on' : 'off'}.</p></div><div><button className="primary-action" onClick={() => downloadReport(report, 'html')}><ArrowDownToLine size={16} />Download HTML report</button><button className="clear-action" onClick={() => downloadReport(report, 'markdown')}><ArrowDownToLine size={15} />Download Markdown</button><p className="lab-note">Open the HTML report and use Print → Save as PDF.</p></div><details><summary>Limitations and coverage</summary><ul>{report.limitations.map(item => <li key={item}>{item}</li>)}</ul><p className="lab-note">Source text SHA256: {report.import.source_sha256}</p></details></section>
      </>}
      <section className="lab-panel import-transcript" ref={transcript}><div className="import-section-heading"><div><p className="eyebrow">THE ORIGINAL THREAD / {preview.anonymized ? 'PARTICIPANT MASKING ON' : 'NAMES VISIBLE'}</p><h2>Read it in order.</h2></div><span className="lab-note">{visible.length} matching entries</span></div><div className="transcript-controls"><label><Search size={15} /><input aria-label="Search imported messages" placeholder="Search words or names" value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} /></label><select aria-label="Filter imported participant" value={speaker} onChange={e => { setSpeaker(e.target.value); setPage(0); }}><option value="all">All participants</option>{preview.participants.map(name => <option key={name}>{name}</option>)}</select><select aria-label="Filter imported message category" value={filter} onChange={e => { setFilter(e.target.value as typeof filter); setPage(0); }}><option value="all">All entries</option>{report && <option value="concern">Needs review</option>}<option value="excluded">Excluded entries</option></select></div><div aria-live="polite">{visible.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE).map(message => renderMessage(message, 'transcript'))}{!visible.length && <p className="lab-note">No entries match these filters.</p>}</div><div className="transcript-pagination"><button disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}><ChevronLeft size={15} />Previous</button><span>Page {currentPage + 1} of {pageCount}</span><button disabled={currentPage >= pageCount - 1} onClick={() => setPage(currentPage + 1)}>Next<ChevronRight size={15} /></button></div></section>
    </>}
    <MessageDetailModal message={selected} onClose={() => setSelected(null)} />
  </section>;
}
