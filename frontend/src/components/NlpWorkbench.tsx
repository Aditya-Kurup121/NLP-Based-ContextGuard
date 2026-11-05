import { useEffect, useState } from 'react';
import { ArrowRight, ExternalLink, FlaskConical } from 'lucide-react';
import { nlpRequest } from '../services/nlp';
import type { Inspection, ModelReport, HostedStatus, HostedReview } from '../services/nlp';

const displayName = (name: string) => name.replaceAll('_', ' ').replace('bow', 'BoW').replace('tfidf', 'TF-IDF');
const percent = (value: number) => (value * 100).toFixed(1) + '%';

export function NlpWorkbench({ conversation }: { conversation: string }) {
  const [tab, setTab] = useState<'language' | 'models' | 'hosted'>('language');
  const [text, setText] = useState(conversation || 'Maya told Jordan: “Please stop calling me an idiot.” They meet in Mumbai on Friday.');
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [tokenIndex, setTokenIndex] = useState<number | null>(null);
  const [report, setReport] = useState<ModelReport | null>(null);
  const [hosted, setHosted] = useState<HostedStatus | null>(null);
  const [hostedResult, setHostedResult] = useState<HostedReview | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [reportError, setReportError] = useState('');
  const [documents, setDocuments] = useState('Please stop teasing me.\nWe are friends.\nPlease respect your friends.');
  const [matrix, setMatrix] = useState<{ vocabulary: string[]; bow: number[][]; tfidf: number[][]; formula: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    nlpRequest<ModelReport>('/evaluation').then(data => { if (!cancelled) setReport(data); }).catch(e => { if (!cancelled) setReportError(e.message); });
    nlpRequest<{ hosted: HostedStatus }>('/status').then(data => { if (!cancelled) setHosted(data.hosted); }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  async function inspect() {
    setBusy(true); setError('');
    try { setInspection(await nlpRequest<Inspection>('/inspect', { text })); setTokenIndex(null); }
    catch (e) { setError(e instanceof Error ? e.message : 'Inspection failed.'); }
    finally { setBusy(false); }
  }
  async function vectorize() {
    setBusy(true); setError('');
    try { setMatrix(await nlpRequest('/vectorize', { documents: documents.split('\n').filter(line => line.trim()) })); }
    catch (e) { setError(e instanceof Error ? e.message : 'Vectorization failed.'); }
    finally { setBusy(false); }
  }
  async function secondOpinion() {
    setBusy(true); setError(''); setHostedResult(null);
    try { setHostedResult(await nlpRequest<HostedReview>('/hosted-review', { conversation: text, consent_to_external_processing: consent })); }
    catch (e) { setError(e instanceof Error ? e.message : 'Hosted review failed.'); }
    finally { setBusy(false); }
  }
  const selectedToken = tokenIndex === null ? null : inspection?.tokens[tokenIndex];
  return <section className="nlp-workbench">
    <div className="lab-header"><div><p className="eyebrow">LOOK UNDER THE HOOD</p><h1>The language lab.</h1><p>Explore the language, inspect the evidence, and compare the methods.</p></div><FlaskConical size={30} strokeWidth={1} /></div>
    <nav className="lab-tabs" aria-label="NLP experiments">{([['language', 'Language lens'], ['models', 'Model evidence'], ['hosted', 'Hosted second opinion']] as const).map(([id, label]) => <button key={id} aria-pressed={tab === id} onClick={() => { setTab(id); setError(''); }}>{label}</button>)}</nav>
    {error && <p className="editor-error" role="alert">{error}</p>}
    {tab !== 'models' && <div className="lab-input"><label htmlFor="lab-text">{tab === 'hosted' ? 'Conversation to send for an independent review' : 'Text to explore'}</label><textarea id="lab-text" value={text} rows={3} maxLength={tab === 'hosted' ? 12000 : 5000} onChange={e => { setText(e.target.value); setInspection(null); setHostedResult(null); setConsent(false); }} /><p className="lab-note">{text.length.toLocaleString()} characters · {tab === 'language' ? 'This inspection runs on your local server.' : 'Only the text shown above will be sent when you explicitly request a hosted review.'}</p></div>}
    {tab === 'language' && <>
      <button className="primary-action" disabled={busy || !text.trim() || text.length > 5000} onClick={inspect}>{busy ? 'Inspecting…' : 'Inspect language'}<ArrowRight size={16} /></button>
      {inspection && <div className="lens-results">
        <section className="lab-panel"><p className="eyebrow">01 / TOKEN EXPLORER</p><h2>Every word has a role.</h2><p className="lab-note">Select a token to inspect its lemma, part of speech, and dependency.</p><div className="token-cloud">{inspection.tokens.map((token, i) => <button key={i} aria-pressed={tokenIndex === i} onClick={() => setTokenIndex(i)}><strong>{token.text}</strong><small>{token.pos}</small></button>)}</div>{selectedToken && <dl className="token-details"><div><dt>Lemma</dt><dd>{selectedToken.lemma}</dd></div><div><dt>Part of speech</dt><dd>{selectedToken.pos}</dd></div><div><dt>Dependency</dt><dd>{selectedToken.dependency}</dd></div><div><dt>Head token</dt><dd>{selectedToken.head}</dd></div></dl>}{!inspection.linguistic_model && <p>{inspection.linguistic_status}</p>}</section>
        <div className="lab-columns"><section className="lab-panel"><p className="eyebrow">02 / ENTITY NOTEBOOK</p><h2>People, places, and more.</h2><div className="entity-list">{inspection.entities.length ? inspection.entities.map((entity, i) => <div key={i}><strong>{entity.text}</strong><span>{entity.label}</span></div>) : <p className="lab-note">No entities were recognized. The model can miss informal names and slang.</p>}</div><p className="lab-note">Extracted from original case and punctuation. An entity mention does not establish who is targeted.</p><h3>Noun phrases</h3><p>{inspection.noun_chunks.map(chunk => chunk.text).join(' · ') || 'None recognized.'}</p></section><section className="lab-panel"><p className="eyebrow">03 / PREPROCESSING</p><h2>Change the text. Keep the meaning.</h2><h3>Normalized</h3><p className="lab-mono">{inspection.normalized}</p><h3>Stopwords filtered, negation retained</h3><p>{inspection.stopword_filtered.join(' ')}</p><h3>Porter stems</h3><p className="lab-mono">{inspection.stemming.porter.join(' · ')}</p><h3>Lancaster stems</h3><p className="lab-mono">{inspection.stemming.lancaster.join(' · ')}</p><p className="lab-note">Vocabulary: {inspection.vocabulary.original} original · {inspection.vocabulary.porter} stems · {inspection.vocabulary.lemmatized ?? '—'} lemmas</p></section></div>
        <section className="lab-panel"><p className="eyebrow">04 / REPRESENTATIONS</p><h2>From characters to phrases.</h2><details><summary>Character tokens ({inspection.tokenization.characters.length})</summary><p className="lab-mono">{inspection.tokenization.characters.slice(0, 300).map(c => c === ' ' ? '␣' : c).join(' · ')}</p></details>{(['wordpiece', 'bpe'] as const).map(method => inspection.tokenization[method] && <details key={method}><summary>{method === 'bpe' ? 'Byte Pair Encoding' : 'WordPiece'} subwords</summary><p className="lab-mono">{inspection.tokenization[method]?.join(' · ')}</p></details>)}{Object.entries(inspection.ngrams).map(([n, grams]) => <details key={n}><summary>{n}-grams ({grams.length} shown)</summary><p className="lab-mono">{grams.join(' / ')}</p></details>)}</section>
      </div>}
      <section className="lab-panel vector-lab"><p className="eyebrow">A SMALL EXPERIMENT / FROM SCRATCH</p><h2>Build a term–document matrix.</h2><label htmlFor="vector-documents">One document per line · up to 5 documents, 500 characters each</label><textarea id="vector-documents" rows={3} value={documents} onChange={e => { setDocuments(e.target.value); setMatrix(null); }} /><button className="clear-action" disabled={busy || !documents.trim()} onClick={vectorize}>Calculate BoW & TF-IDF <ArrowRight size={15} /></button>{matrix && <><div className="table-scroll"><table><caption>TF-IDF weights · hover a weight to see its raw count</caption><thead><tr><th>Document</th>{matrix.vocabulary.map(word => <th key={word}>{word}</th>)}</tr></thead><tbody>{matrix.tfidf.map((row, i) => <tr key={i}><th>D{i + 1}</th>{row.map((value, j) => <td key={j} title={`BoW count: ${matrix.bow[i][j]}`}>{value.toFixed(2)}</td>)}</tr>)}</tbody></table></div><p className="lab-note">{matrix.formula}</p></>}</section>
    </>}
    {tab === 'models' && <>{reportError && <p role="alert">{reportError}</p>}{report && <>
      <section className="lab-panel"><p className="eyebrow">HELD-OUT RESULTS / NOT THE DEMO BENCHMARK</p><h2>Measure the model, including its mistakes.</h2><p>{report.task}.</p><div className="split-strip">{Object.entries(report.split_sizes).map(([name, count]) => <div key={name}><span>{name}</span><strong>{count.toLocaleString()}</strong></div>)}</div><p className="lab-note">{report.exact_cross_split_duplicates_removed} exact normalized duplicates removed across source splits. Selection uses validation macro-F1; test results are reported after selection.</p><div className="table-scroll"><table><caption>Higher is better. Accuracy alone hides the imbalanced classes.</caption><thead><tr><th>Method</th><th>Validation macro-F1</th><th>Test macro-F1</th><th>Toxic precision</th><th>Toxic recall</th><th>Test accuracy</th></tr></thead><tbody><tr><th>Majority baseline</th><td>—</td><td>{report.majority_baseline.macro_f1.toFixed(3)}</td><td>{percent(report.majority_baseline.per_class.toxic.precision)}</td><td>{percent(report.majority_baseline.per_class.toxic.recall)}</td><td>{percent(report.majority_baseline.accuracy)}</td></tr>{Object.entries(report.models).map(([name, scores]) => <tr key={name} className={name === report.selected_model ? 'selected-model' : ''}><th>{displayName(name)}{name === report.selected_model && <small>SELECTED ON VALIDATION</small>}</th><td>{scores.validation.macro_f1.toFixed(3)}</td><td>{scores.test.macro_f1.toFixed(3)}</td><td>{percent(scores.test.per_class.toxic.precision)}</td><td>{percent(scores.test.per_class.toxic.recall)}</td><td>{percent(scores.test.accuracy)}</td></tr>)}</tbody></table></div><h3>Selected model’s confusion matrix</h3><p className="lab-note">Rows = actual label; columns = predicted label. Order: not toxic, toxic.</p><div className="confusion-grid">{report.models[report.selected_model].test.confusion_matrix.flatMap((row, i) => row.map((value, j) => <div key={`${i}-${j}`} className={i === j ? 'correct-cell' : 'error-cell'}><span>{i === 0 ? 'Not toxic' : 'Toxic'} → {j === 0 ? 'not toxic' : 'toxic'}</span><strong>{value.toLocaleString()}</strong></div>))}</div><ul className="lab-limitations">{report.limitations.map(item => <li key={item}>{item}</li>)}</ul><a className="source-link" href={report.source_url} target="_blank" rel="noreferrer">View dataset source <ExternalLink size={13} /></a><p className="lab-note">Dataset revision: {report.dataset_revision}</p></section>
    </>}</>}
    {tab === 'hosted' && <section className="lab-panel"><p className="eyebrow">AN OPTIONAL SECOND PERSPECTIVE</p><h2>Compare a generated review.</h2><p>A hosted language model reviews the conversation independently. It can disagree with the local engine and can be wrong.</p>{hosted?.configured ? <><p className="lab-note">Provider: {hosted.provider} · Model: {hosted.model}</p><label className="consent-checkbox"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} />I agree to send the text above to Hugging Face and its inference provider. API charges may apply.</label><button className="primary-action" disabled={!consent || busy || !text.trim() || text.length > 12000} onClick={secondOpinion}>{busy ? 'Requesting review…' : 'Send for hosted review'}<ArrowRight size={16} /></button></> : <p className="hosted-unavailable">Hosted review has not been configured. Local analysis and the language lab work without it. Setup instructions are in the project’s NLP guide.</p>}{hostedResult && <div className="hosted-result"><h3>{hostedResult.risk} · generated assessment</h3><p>{hostedResult.summary}</p>{hostedResult.evidence.map((item, i) => <blockquote key={i}><strong>“{item.quote}”</strong><p>{item.explanation}</p></blockquote>)}<h3>Another possible interpretation</h3><p>{hostedResult.alternative_interpretation}</p><h3>Suggested next step</h3><p>{hostedResult.suggested_action}</p><p className="lab-note">{hostedResult.note}</p></div>}</section>}
  </section>;
}
