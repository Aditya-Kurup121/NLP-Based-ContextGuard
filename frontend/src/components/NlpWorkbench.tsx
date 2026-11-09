import { useEffect, useState } from 'react';
import {
  ArrowRight,
  ExternalLink,
  FlaskConical,
  Layers,
  Sparkles,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { nlpRequest } from '../services/nlp';
import type {
  Inspection,
  ModelReport,
  HostedStatus,
  HostedReview,
  LevenshteinResult,
  Word2VecStatus,
  WordNeighbor,
  WordAnalogyResult,
} from '../services/nlp';

const displayName = (name: string) =>
  name.replaceAll('_', ' ').replace('bow', 'BoW').replace('tfidf', 'TF-IDF').replace('distilbert', 'DistilBERT');
const percent = (value: number) => (value * 100).toFixed(1) + '%';

export function NlpWorkbench({ conversation }: { conversation: string }) {
  // Main Lab Tabs
  const [activeLab, setActiveLab] = useState<
    'preprocessing' | 'features' | 'embeddings' | 'pos_ner' | 'models' | 'hosted'
  >('preprocessing');

  // Shared text state
  const [text, setText] = useState(
    conversation ||
      'Maya told Jordan: "Please stop calling me an idiot." They meet in Mumbai on Friday. Check https://example.com'
  );
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [tokenIndex, setTokenIndex] = useState<number | null>(null);
  const [report, setReport] = useState<ModelReport | null>(null);
  const [reportError, setReportError] = useState('');
  const [hosted, setHosted] = useState<HostedStatus | null>(null);
  const [hostedResult, setHostedResult] = useState<HostedReview | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // CO2: Vectorization & Levenshtein states
  const [documents, setDocuments] = useState(
    'Please stop teasing me.\nWe are close friends.\nPlease respect your peers.'
  );
  const [matrix, setMatrix] = useState<{
    vocabulary: string[];
    bow: number[][];
    tfidf: number[][];
    formula: string;
  } | null>(null);
  const [levStr1, setLevStr1] = useState('cyberbullying');
  const [levStr2, setLevStr2] = useState('cyberbully');
  const [levResult, setLevResult] = useState<LevenshteinResult | null>(null);

  // CO2: Word2Vec states
  const [w2vStatus, setW2vStatus] = useState<Word2VecStatus | null>(null);
  // Set after retraining; queries then use this user's own model instead of the shared default.
  const w2vModelId = w2vStatus?.model_id;
  const [w2vQueryWord, setW2vQueryWord] = useState('friend');
  const [w2vVector, setW2vVector] = useState<{ word: string; dimensions: number; vector: number[] } | null>(null);
  const [simWord1, setSimWord1] = useState('friend');
  const [simWord2, setSimWord2] = useState('peer');
  const [simResult, setSimResult] = useState<{ word1: string; word2: string; cosine_similarity: number; interpretation: string } | null>(null);
  const [neighborQuery, setNeighborQuery] = useState('threat');
  const [neighbors, setNeighbors] = useState<WordNeighbor[] | null>(null);
  const [analogyA, setAnalogyA] = useState('man');
  const [analogyB, setAnalogyB] = useState('king');
  const [analogyC, setAnalogyC] = useState('woman');
  const [analogyResult, setAnalogyResult] = useState<WordAnalogyResult | null>(null);
  const [customCorpus, setCustomCorpus] = useState(
    'friends support each other\ncyberbullying causes harm and distress\nbystanders defend victims\nlaughter and humor are friendly'
  );

  // Initial fetch for model report & backend status
  useEffect(() => {
    let cancelled = false;
    nlpRequest<ModelReport>('/evaluation')
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((e) => {
        if (!cancelled) setReportError(e.message);
      });

    nlpRequest<{ hosted: HostedStatus }>('/status')
      .then((data) => {
        if (!cancelled) setHosted(data.hosted);
      })
      .catch(() => {});

    nlpRequest<Word2VecStatus>('/word2vec/status')
      .then((data) => {
        if (!cancelled) setW2vStatus(data);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, []);

  // Handlers
  async function runInspect() {
    setBusy(true);
    setError('');
    try {
      const res = await nlpRequest<Inspection>('/inspect', { text });
      setInspection(res);
      setTokenIndex(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Inspection failed.');
    } finally {
      setBusy(false);
    }
  }

  async function runVectorize() {
    setBusy(true);
    setError('');
    try {
      const docs = documents.split('\n').filter((line) => line.trim());
      const res = await nlpRequest<{ vocabulary: string[]; bow: number[][]; tfidf: number[][]; formula: string }>(
        '/vectorize',
        { documents: docs }
      );
      setMatrix(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Vectorization failed.');
    } finally {
      setBusy(false);
    }
  }

  async function runLevenshtein() {
    setBusy(true);
    setError('');
    try {
      const res = await nlpRequest<LevenshteinResult>('/levenshtein', { str1: levStr1, str2: levStr2 });
      setLevResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Levenshtein calculation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function fetchW2vVector() {
    setBusy(true);
    setError('');
    try {
      const res = await nlpRequest<{ word: string; dimensions: number; vector: number[] }>('/word2vec/vector', {
        word: w2vQueryWord,
        model_id: w2vModelId,
      });
      setW2vVector(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to retrieve word vector.');
    } finally {
      setBusy(false);
    }
  }

  async function fetchW2vSimilarity() {
    setBusy(true);
    setError('');
    try {
      const res = await nlpRequest<{ word1: string; word2: string; cosine_similarity: number; interpretation: string }>(
        '/word2vec/similarity',
        { word1: simWord1, word2: simWord2, model_id: w2vModelId }
      );
      setSimResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Cosine similarity calculation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function fetchW2vNeighbors() {
    setBusy(true);
    setError('');
    try {
      const res = await nlpRequest<{ query: string; nearest_neighbors: WordNeighbor[] }>('/word2vec/similar', {
        word: neighborQuery,
        top_n: 6,
        model_id: w2vModelId,
      });
      setNeighbors(res.nearest_neighbors);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Nearest neighbors search failed.');
    } finally {
      setBusy(false);
    }
  }

  async function fetchW2vAnalogy() {
    setBusy(true);
    setError('');
    try {
      const res = await nlpRequest<WordAnalogyResult>('/word2vec/analogy', {
        a: analogyA,
        b: analogyB,
        c: analogyC,
        model_id: w2vModelId,
      });
      setAnalogyResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Word analogy calculation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function runW2vRetrain() {
    setBusy(true);
    setError('');
    try {
      const lines = customCorpus.split('\n').filter((l) => l.trim());
      const res = await nlpRequest<Word2VecStatus>('/word2vec/train', { corpus: lines, epochs: 40 });
      setW2vStatus(res);
      setW2vVector(null);
      setSimResult(null);
      setNeighbors(null);
      setAnalogyResult(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Word2Vec retraining failed.');
    } finally {
      setBusy(false);
    }
  }

  async function runSecondOpinion() {
    setBusy(true);
    setError('');
    setHostedResult(null);
    try {
      const res = await nlpRequest<HostedReview>('/hosted-review', {
        conversation: text,
        consent_to_external_processing: consent,
      });
      setHostedResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Hosted review failed.');
    } finally {
      setBusy(false);
    }
  }

  const selectedToken = tokenIndex === null ? null : inspection?.tokens[tokenIndex];

  return (
    <section className="nlp-workbench space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="lab-header glass-panel p-6 sm:p-8 rounded-2xl border border-stone-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="eyebrow">ACADEMIC NLP LABORATORY (CO1 — CO5)</p>
          <h1 className="text-2xl sm:text-4xl font-serif text-stone-900 font-normal">
            The NLP Workbench
          </h1>
          <p className="text-stone-600 text-xs sm:text-sm mt-1">
            Interactive experimental workbench covering text preprocessing, word representations, POS/NER tagging, text classification, and LLM deployment.
          </p>
        </div>
        <div className="p-3 bg-emerald-800/10 rounded-2xl text-emerald-800">
          <FlaskConical size={32} strokeWidth={1.5} />
        </div>
      </div>

      {/* Navigation Tabs for all 5 Course Outcomes */}
      <nav className="lab-tabs flex gap-4 border-b border-stone-200 overflow-x-auto pb-1" aria-label="NLP Experiments">
        {(
          [
            ['preprocessing', '01 / Preprocessing (CO1)'],
            ['features', '02 / Features & Vectors (CO2)'],
            ['embeddings', '03 / Word Embeddings (CO2)'],
            ['pos_ner', '04 / POS & NER (CO3)'],
            ['models', '05 / Classification (CO4)'],
            ['hosted', '06 / Hosted LLM (CO5)'],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            aria-pressed={activeLab === id}
            className={`py-3 px-3 text-xs sm:text-sm font-medium border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
              activeLab === id
                ? 'border-emerald-800 text-emerald-800 font-semibold'
                : 'border-transparent text-stone-500 hover:text-stone-800'
            }`}
            onClick={() => {
              setActiveLab(id);
              setError('');
            }}
          >
            {label}
          </button>
        ))}
      </nav>

      {error && (
        <div className="editor-error flex items-center gap-2 p-3 bg-red-50 border border-red-200 text-red-800 text-xs rounded-xl" role="alert">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Shared Text Input (for Preprocessing, POS/NER, and LLM) */}
      {activeLab !== 'models' && activeLab !== 'embeddings' && (
        <div className="lab-input glass-panel p-5 rounded-2xl border border-stone-200">
          <div className="flex justify-between items-center mb-2">
            <label htmlFor="lab-text" className="text-xs font-bold uppercase tracking-wider text-stone-700">
              {activeLab === 'hosted'
                ? 'Conversation transcript for external LLM review'
                : 'Text for linguistic inspection (CO1, CO2, CO3)'}
            </label>
            <span className="text-xs text-stone-500">{text.length.toLocaleString()} characters</span>
          </div>
          <textarea
            id="lab-text"
            value={text}
            rows={3}
            maxLength={activeLab === 'hosted' ? 12000 : 5000}
            className="w-full p-3 font-mono text-xs bg-stone-50 border border-stone-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-emerald-700"
            onChange={(e) => {
              setText(e.target.value);
              setInspection(null);
              setHostedResult(null);
              setConsent(false);
            }}
          />
          <div className="flex justify-between items-center mt-3">
            <p className="lab-note text-[11px] text-stone-500">
              {activeLab === 'hosted'
                ? 'Only this explicitly submitted transcript will be sent to Hugging Face upon checking consent.'
                : 'Runs locally on CPU via FastAPI, spaCy, NLTK, and custom Python algorithms.'}
            </p>
            {activeLab !== 'hosted' && (
              <button
                className="primary-action px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded-xl flex items-center gap-2 transition cursor-pointer disabled:opacity-50"
                disabled={busy || !text.trim() || text.length > 5000}
                onClick={runInspect}
              >
                {busy ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>Execute NLP Pipeline</span>
                    <ArrowRight size={14} />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* LAB 1: TEXT PREPROCESSING (CO1)                                          */}
      {/* ========================================================================= */}
      {activeLab === 'preprocessing' && (
        <div className="space-y-6">
          {!inspection && (
            <div className="glass-panel p-8 rounded-2xl border border-stone-200 text-center">
              <Sparkles className="w-8 h-8 text-emerald-700 mx-auto mb-2 opacity-80" />
              <h3 className="text-base font-serif font-bold text-stone-800">Execute Preprocessing</h3>
              <p className="text-xs text-stone-600 max-w-md mx-auto mt-1">
                Click <strong>Execute NLP Pipeline</strong> above to inspect sentence segmentation, tokenization, noise removal, Porter/Lancaster stems, and negation-retaining stopwords.
              </p>
            </div>
          )}

          {inspection && (
            <div className="space-y-6">
              {/* Cleaning & Normalization Before-After */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <section className="lab-panel p-5 rounded-2xl border border-stone-200 bg-white">
                  <p className="eyebrow text-[10px] text-stone-500 font-mono">01 / NOISE REMOVAL & UNICODE</p>
                  <h3 className="font-serif font-bold text-base text-stone-900 mb-2">Text Cleaning</h3>
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-stone-500 block font-semibold">Original Raw Text:</span>
                      <p className="p-2.5 bg-stone-100 rounded font-mono text-[11px] break-all">{inspection.original}</p>
                    </div>
                    <div>
                      <span className="text-stone-500 block font-semibold">Noise Removed (Stripped HTML, Zero-Width & Control Chars):</span>
                      <p className="p-2.5 bg-emerald-50/60 rounded font-mono text-[11px] text-emerald-950 break-all">{inspection.noise_removed}</p>
                    </div>
                    <div>
                      <span className="text-stone-500 block font-semibold">NFKC Normalized (Lowercased, Canonical URLs & Emails):</span>
                      <p className="p-2.5 bg-stone-100 rounded font-mono text-[11px] text-stone-800 break-all">{inspection.normalized}</p>
                    </div>
                  </div>
                </section>

                <section className="lab-panel p-5 rounded-2xl border border-stone-200 bg-white">
                  <p className="eyebrow text-[10px] text-stone-500 font-mono">02 / STOPWORDS & NEGATION PRESERVATION</p>
                  <h3 className="font-serif font-bold text-base text-stone-900 mb-2">Polarity-Preserving Filter</h3>
                  <p className="text-xs text-stone-600 mb-3">
                    Crucial for sentiment & cyberbullying: words like <em>not</em>, <em>never</em>, and <em>n't</em> are explicitly preserved while neutral stopwords are removed.
                  </p>
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-stone-500 block font-semibold mb-1">Preserved Negation Tokens (Kept):</span>
                      <div className="flex flex-wrap gap-1.5">
                        {inspection.stopword_analysis?.preserved_negations.length ? (
                          inspection.stopword_analysis.preserved_negations.map((neg, i) => (
                            <span key={i} className="px-2 py-0.5 bg-emerald-100 text-emerald-900 font-mono text-[11px] rounded border border-emerald-300">
                              ✓ {neg}
                            </span>
                          ))
                        ) : (
                          <span className="text-stone-400 italic">No negation words detected in this text.</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <span className="text-stone-500 block font-semibold mb-1">Removed Stopwords:</span>
                      <div className="flex flex-wrap gap-1">
                        {inspection.stopword_analysis?.removed_stopwords.map((sw, i) => (
                          <span key={i} className="px-1.5 py-0.5 bg-stone-100 text-stone-600 line-through font-mono text-[10px] rounded">
                            {sw}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-stone-500 block font-semibold">Resulting Filtered String:</span>
                      <p className="p-2 bg-stone-50 rounded font-mono text-[11px] text-stone-800">
                        {inspection.stopword_filtered.join(' ')}
                      </p>
                    </div>
                  </div>
                </section>
              </div>

              {/* Tokenization Showcase */}
              <section className="lab-panel p-5 rounded-2xl border border-stone-200 bg-white">
                <p className="eyebrow text-[10px] text-stone-500 font-mono">03 / MULTI-LEVEL TOKENIZATION</p>
                <h3 className="font-serif font-bold text-base text-stone-900 mb-2">Sentences, Words, Characters & Subwords</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <h4 className="font-semibold text-stone-700 mb-1">Sentence Segmentation ({inspection.tokenization.sentences?.length || 1})</h4>
                    <ol className="list-decimal list-inside space-y-1 p-2 bg-stone-50 rounded">
                      {inspection.tokenization.sentences?.map((s, i) => (
                        <li key={i} className="font-mono text-[11px] text-stone-800">{s}</li>
                      ))}
                    </ol>

                    <h4 className="font-semibold text-stone-700 mt-3 mb-1">Word Tokens ({inspection.tokenization.word_and_punctuation.length})</h4>
                    <div className="flex flex-wrap gap-1 p-2 bg-stone-50 rounded max-h-32 overflow-y-auto">
                      {inspection.tokenization.word_and_punctuation.map((w, i) => (
                        <span key={i} className="px-1.5 py-0.5 bg-white border border-stone-200 rounded font-mono text-[10px]">{w}</span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-stone-700 mb-1">Subword Tokenization (BPE & WordPiece)</h4>
                    <div className="space-y-2">
                      <div>
                        <span className="text-[10px] text-stone-500 uppercase font-mono block">WordPiece Subwords:</span>
                        <div className="flex flex-wrap gap-1 p-2 bg-stone-50 rounded max-h-24 overflow-y-auto font-mono text-[10px]">
                          {inspection.tokenization.wordpiece ? (
                            inspection.tokenization.wordpiece.map((t, i) => (
                              <span key={i} className="px-1.5 py-0.5 bg-amber-50 text-amber-900 border border-amber-200 rounded">{t}</span>
                            ))
                          ) : (
                            <span className="text-stone-400">WordPiece tokenizer artifact not loaded.</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] text-stone-500 uppercase font-mono block">Byte-Pair Encoding (BPE):</span>
                        <div className="flex flex-wrap gap-1 p-2 bg-stone-50 rounded max-h-24 overflow-y-auto font-mono text-[10px]">
                          {inspection.tokenization.bpe ? (
                            inspection.tokenization.bpe.map((t, i) => (
                              <span key={i} className="px-1.5 py-0.5 bg-indigo-50 text-indigo-900 border border-indigo-200 rounded">{t}</span>
                            ))
                          ) : (
                            <span className="text-stone-400">BPE tokenizer artifact not loaded.</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              {/* Stemming vs Lemmatization Comparison */}
              <section className="lab-panel p-5 rounded-2xl border border-stone-200 bg-white">
                <p className="eyebrow text-[10px] text-stone-500 font-mono">04 / STEMMING VS LEMMATIZATION</p>
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-serif font-bold text-base text-stone-900">Morphological Reduction</h3>
                  <div className="text-xs text-stone-500 space-x-3">
                    <span>Original: <strong>{inspection.vocabulary.original}</strong> unique words</span>
                    <span>•</span>
                    <span>Porter: <strong>{inspection.vocabulary.porter}</strong> stems</span>
                    <span>•</span>
                    <span>Lemmas: <strong>{inspection.vocabulary.lemmatized || '—'}</strong> roots</span>
                  </div>
                </div>

                <div className="table-scroll max-h-64 overflow-y-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-stone-100 sticky top-0">
                      <tr>
                        <th className="p-2 border-b">Token</th>
                        <th className="p-2 border-b">Porter Stem</th>
                        <th className="p-2 border-b">Lancaster Stem</th>
                        <th className="p-2 border-b">spaCy Lemma</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inspection.tokenization.word_and_punctuation.slice(0, 20).map((tok, i) => (
                        <tr key={i} className="border-b border-stone-100 hover:bg-stone-50 font-mono text-[11px]">
                          <td className="p-2 font-semibold text-stone-900">{tok}</td>
                          <td className="p-2 text-stone-600">{inspection.stemming.porter[i] || '—'}</td>
                          <td className="p-2 text-stone-600">{inspection.stemming.lancaster[i] || '—'}</td>
                          <td className="p-2 text-emerald-800 font-semibold">{inspection.tokens[i]?.lemma || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* LAB 2: FEATURE EXTRACTION & VECTORIZATION (CO2)                           */}
      {/* ========================================================================= */}
      {activeLab === 'features' && (
        <div className="space-y-6">
          {/* Levenshtein Edit Distance Tool */}
          <section className="lab-panel p-6 rounded-2xl border border-stone-200 bg-white">
            <p className="eyebrow text-[10px] text-stone-500 font-mono">01 / STRING METRICS</p>
            <h3 className="font-serif font-bold text-lg text-stone-900 mb-1">Levenshtein Edit Distance Calculator</h3>
            <p className="text-xs text-stone-600 mb-4">
              Measures the minimum number of single-character edits (insertions, deletions, or substitutions) required to transform one string into another. Useful for typos and obfuscated profanity detection.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
              <div>
                <label className="text-[11px] font-semibold text-stone-700 block mb-1">String 1</label>
                <input
                  type="text"
                  value={levStr1}
                  className="w-full p-2 border border-stone-200 rounded-xl font-mono text-xs"
                  onChange={(e) => setLevStr1(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-stone-700 block mb-1">String 2</label>
                <input
                  type="text"
                  value={levStr2}
                  className="w-full p-2 border border-stone-200 rounded-xl font-mono text-xs"
                  onChange={(e) => setLevStr2(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={runLevenshtein}
                  disabled={busy || !levStr1 || !levStr2}
                  className="w-full primary-action px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded-xl flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {busy ? 'Computing...' : 'Calculate Distance'}
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>

            {levResult && (
              <div className="p-4 bg-stone-50 rounded-xl border border-stone-200 space-y-3 text-xs">
                <div className="flex flex-wrap gap-6 items-center">
                  <div>
                    <span className="text-stone-500 block uppercase text-[10px]">Edit Distance</span>
                    <strong className="text-2xl font-serif text-stone-900">{levResult.distance}</strong>
                  </div>
                  <div>
                    <span className="text-stone-500 block uppercase text-[10px]">Similarity Ratio</span>
                    <strong className="text-2xl font-serif text-emerald-800">
                      {(levResult.similarity_ratio * 100).toFixed(1)}%
                    </strong>
                  </div>
                  <div className="flex-1">
                    <span className="text-stone-500 block uppercase text-[10px]">Edit Sequence</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {levResult.operations.map((op, i) => (
                        <span
                          key={i}
                          className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${
                            op.op === 'match'
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : op.op === 'substitute'
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-red-50 text-red-800 border-red-200'
                          }`}
                        >
                          {op.op}: {op.char1}➔{op.char2}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* DP Cost Matrix (Accordion / preview) */}
                <details className="mt-2 text-stone-600">
                  <summary className="cursor-pointer font-semibold text-[11px] text-stone-700">
                    View Dynamic Programming Cost Matrix ({levResult.header_y.length} × {levResult.header_x.length})
                  </summary>
                  <div className="table-scroll mt-2 max-h-48 overflow-auto">
                    <table className="border-collapse text-[11px] font-mono">
                      <thead>
                        <tr>
                          {levResult.header_x.map((ch, idx) => (
                            <th key={idx} className="p-1 border bg-stone-100 text-center">{ch}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {levResult.matrix.map((row, rIdx) => (
                          <tr key={rIdx}>
                            <th className="p-1 border bg-stone-100 text-center font-bold">{levResult.header_y[rIdx]}</th>
                            {row.map((val, cIdx) => (
                              <td key={cIdx} className="p-1 border text-center">{val}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              </div>
            )}
          </section>

          {/* Bag of Words & TF-IDF Term-Document Matrix */}
          <section className="lab-panel p-6 rounded-2xl border border-stone-200 bg-white">
            <p className="eyebrow text-[10px] text-stone-500 font-mono">02 / VECTOR SPACE MODEL</p>
            <h3 className="font-serif font-bold text-lg text-stone-900 mb-1">From-Scratch Term–Document Matrix</h3>
            <p className="text-xs text-stone-600 mb-3">
              Computes raw Count Bag-of-Words and mathematical TF-IDF (smooth logarithmic formula) across user-provided sentences.
            </p>

            <label htmlFor="vector-documents" className="block text-[11px] font-semibold text-stone-700 mb-1">
              One document per line (up to 5 documents, 500 characters each)
            </label>
            <textarea
              id="vector-documents"
              rows={3}
              value={documents}
              className="w-full p-3 font-mono text-xs bg-stone-50 border border-stone-200 rounded-xl mb-3 focus:outline-none"
              onChange={(e) => {
                setDocuments(e.target.value);
                setMatrix(null);
              }}
            />
            <button
              className="primary-action px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded-xl flex items-center gap-2 cursor-pointer disabled:opacity-50"
              disabled={busy || !documents.trim()}
              onClick={runVectorize}
            >
              {busy ? 'Computing...' : 'Calculate BoW & TF-IDF'}
              <ArrowRight size={14} />
            </button>

            {matrix && (
              <div className="mt-4 space-y-3">
                <div className="table-scroll border border-stone-200 rounded-xl overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-stone-100">
                      <tr>
                        <th className="p-2 border-b">Document</th>
                        {matrix.vocabulary.map((w) => (
                          <th key={w} className="p-2 border-b font-mono font-normal text-stone-700">{w}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {matrix.tfidf.map((row, i) => (
                        <tr key={i} className="border-b border-stone-100 hover:bg-stone-50">
                          <th className="p-2 font-mono font-bold text-stone-800 bg-stone-50/50">Doc {i + 1}</th>
                          {row.map((val, j) => (
                            <td key={j} className="p-2 font-mono text-[11px]" title={`BoW count: ${matrix.bow[i][j]}`}>
                              <span className="text-emerald-900 font-semibold">{val.toFixed(2)}</span>
                              <span className="text-[10px] text-stone-400 block">ct: {matrix.bow[i][j]}</span>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-[11px] text-stone-500 font-mono italic">
                  Formula: {matrix.formula}
                </p>
              </div>
            )}
          </section>

          {/* N-Grams and Regex Entities */}
          {inspection && (
            <section className="lab-panel p-6 rounded-2xl border border-stone-200 bg-white">
              <p className="eyebrow text-[10px] text-stone-500 font-mono">03 / N-GRAMS & REGEX PATTERNS</p>
              <h3 className="font-serif font-bold text-lg text-stone-900 mb-2">Lexical Sequences & Patterns</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                {(['1', '2', '3'] as const).map((n) => (
                  <div key={n} className="p-3 bg-stone-50 rounded-xl border border-stone-200">
                    <h4 className="font-bold text-stone-800 mb-1">{n}-Grams ({inspection.ngrams[n]?.length || 0})</h4>
                    <div className="max-h-36 overflow-y-auto space-y-1 font-mono text-[11px] text-stone-700">
                      {inspection.ngrams[n]?.slice(0, 15).map((gram, i) => (
                        <div key={i} className="truncate">"{gram}"</div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* LAB 3: WORD EMBEDDINGS (WORD2VEC) (CO2)                                  */}
      {/* ========================================================================= */}
      {activeLab === 'embeddings' && (
        <div className="space-y-6">
          {/* Word2Vec Model Status */}
          <section className="lab-panel p-6 rounded-2xl border border-stone-200 bg-white">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-3">
              <div>
                <p className="eyebrow text-[10px] text-stone-500 font-mono">DENSE WORD REPRESENTATIONS</p>
                <h3 className="font-serif font-bold text-xl text-stone-900">Word2Vec (Skip-gram with Negative Sampling)</h3>
                <p className="text-xs text-stone-600 mt-1">
                  Learns continuous dense vector representations where semantically related words are located close to each other in vector space.
                </p>
              </div>
              {w2vStatus && (
                <div className="flex gap-4 text-center">
                  <div className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-xl">
                    <span className="text-[10px] uppercase font-mono text-emerald-800 block">Vocab</span>
                    <strong className="text-lg font-serif text-emerald-950">{w2vStatus.vocabulary_size}</strong>
                  </div>
                  <div className="px-3 py-1.5 bg-stone-100 border border-stone-200 rounded-xl">
                    <span className="text-[10px] uppercase font-mono text-stone-600 block">Dimension</span>
                    <strong className="text-lg font-serif text-stone-900">{w2vStatus.embedding_dim}-d</strong>
                  </div>
                </div>
              )}
            </div>

            {w2vStatus && (
              <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 text-xs text-stone-600 mb-4">
                <strong>Sample Vocabulary:</strong>{' '}
                <span className="font-mono text-[11px] text-stone-800">{w2vStatus.sample_words.join(', ')} ...</span>
              </div>
            )}

            {/* Sub-grid: 1) Cosine Similarity, 2) Nearest Neighbors, 3) Word Analogies */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              {/* Tool A: Cosine Similarity */}
              <div className="p-4 bg-stone-50 rounded-xl border border-stone-200 space-y-2">
                <h4 className="font-bold text-stone-800">Cosine Similarity</h4>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={simWord1}
                    className="p-1.5 border rounded bg-white text-xs font-mono"
                    onChange={(e) => setSimWord1(e.target.value)}
                    placeholder="word1"
                  />
                  <input
                    type="text"
                    value={simWord2}
                    className="p-1.5 border rounded bg-white text-xs font-mono"
                    onChange={(e) => setSimWord2(e.target.value)}
                    placeholder="word2"
                  />
                </div>
                <button
                  onClick={fetchW2vSimilarity}
                  disabled={busy || !simWord1 || !simWord2}
                  className="w-full py-1.5 bg-emerald-800 text-white rounded font-semibold text-[11px] cursor-pointer"
                >
                  Compute Similarity
                </button>
                {simResult && (
                  <div className="p-2 bg-white rounded border border-emerald-200 text-[11px]">
                    <div className="flex justify-between items-center">
                      <span className="text-stone-600">cos(θ):</span>
                      <strong className="font-mono text-emerald-900 text-sm">{simResult.cosine_similarity}</strong>
                    </div>
                    <span className="text-[10px] text-stone-500 block mt-1">{simResult.interpretation}</span>
                  </div>
                )}
              </div>

              {/* Tool B: Nearest Neighbors */}
              <div className="p-4 bg-stone-50 rounded-xl border border-stone-200 space-y-2">
                <h4 className="font-bold text-stone-800">Nearest Neighbors</h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={neighborQuery}
                    className="flex-1 p-1.5 border rounded bg-white text-xs font-mono"
                    onChange={(e) => setNeighborQuery(e.target.value)}
                    placeholder="target word"
                  />
                  <button
                    onClick={fetchW2vNeighbors}
                    disabled={busy || !neighborQuery}
                    className="px-3 py-1.5 bg-emerald-800 text-white rounded font-semibold text-[11px] cursor-pointer"
                  >
                    Find
                  </button>
                </div>
                {neighbors && (
                  <div className="p-2 bg-white rounded border border-stone-200 text-[11px] max-h-36 overflow-y-auto space-y-1">
                    {neighbors.map((n, i) => (
                      <div key={i} className="flex justify-between font-mono">
                        <span>{n.word}</span>
                        <strong className="text-emerald-800">{n.similarity}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Tool C: Word Analogy */}
              <div className="p-4 bg-stone-50 rounded-xl border border-stone-200 space-y-2">
                <h4 className="font-bold text-stone-800">Word Analogy (A:B :: C:?)</h4>
                <div className="grid grid-cols-3 gap-1">
                  <input
                    type="text"
                    value={analogyA}
                    className="p-1 border rounded bg-white text-[11px] font-mono"
                    onChange={(e) => setAnalogyA(e.target.value)}
                    placeholder="A"
                  />
                  <input
                    type="text"
                    value={analogyB}
                    className="p-1 border rounded bg-white text-[11px] font-mono"
                    onChange={(e) => setAnalogyB(e.target.value)}
                    placeholder="B"
                  />
                  <input
                    type="text"
                    value={analogyC}
                    className="p-1 border rounded bg-white text-[11px] font-mono"
                    onChange={(e) => setAnalogyC(e.target.value)}
                    placeholder="C"
                  />
                </div>
                <button
                  onClick={fetchW2vAnalogy}
                  disabled={busy || !analogyA || !analogyB || !analogyC}
                  className="w-full py-1.5 bg-emerald-800 text-white rounded font-semibold text-[11px] cursor-pointer"
                >
                  Solve Analogy
                </button>
                {analogyResult && (
                  <div className="p-2 bg-white rounded border border-stone-200 text-[11px] space-y-1">
                    <span className="text-[10px] text-stone-500 block">{analogyResult.analogy}</span>
                    {analogyResult.results.map((r, i) => (
                      <div key={i} className="flex justify-between font-mono">
                        <strong className="text-stone-900">{r.word}</strong>
                        <span className="text-emerald-800">{r.similarity}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Word Vector Inspector */}
            <div className="mt-4 pt-4 border-t border-stone-200">
              <h4 className="text-xs font-bold text-stone-800 mb-1">Embedding Vector Inspector</h4>
              <div className="flex gap-2 max-w-sm mb-2">
                <input
                  type="text"
                  value={w2vQueryWord}
                  className="flex-1 p-2 border border-stone-200 rounded-xl text-xs font-mono"
                  onChange={(e) => setW2vQueryWord(e.target.value)}
                  placeholder="Enter word"
                />
                <button
                  onClick={fetchW2vVector}
                  disabled={busy || !w2vQueryWord}
                  className="px-4 py-2 bg-stone-800 text-white text-xs font-semibold rounded-xl cursor-pointer"
                >
                  View Vector
                </button>
              </div>

              {w2vVector && (
                <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 text-xs">
                  <span className="text-[10px] text-stone-500 uppercase font-mono block mb-1">
                    Normalized 32-dimensional vector for "{w2vVector.word}":
                  </span>
                  <p className="font-mono text-[10px] text-stone-700 break-all bg-white p-2 rounded border">
                    [{w2vVector.vector.join(', ')}]
                  </p>
                </div>
              )}
            </div>

            {/* Custom Corpus Retraining Drawer */}
            <details className="mt-4 pt-4 border-t border-stone-200 text-xs">
              <summary className="font-semibold text-stone-800 cursor-pointer">
                Train on Custom Corpus (Experimental)
              </summary>
              <div className="mt-2 space-y-2">
                <textarea
                  rows={3}
                  value={customCorpus}
                  className="w-full p-2 border rounded-xl font-mono text-xs bg-stone-50"
                  onChange={(e) => setCustomCorpus(e.target.value)}
                />
                <button
                  onClick={runW2vRetrain}
                  disabled={busy || !customCorpus.trim()}
                  className="px-4 py-2 bg-emerald-800 text-white rounded-xl text-xs font-semibold cursor-pointer"
                >
                  {busy ? 'Training Word2Vec...' : 'Retrain Skip-gram Model'}
                </button>
              </div>
            </details>
          </section>
        </div>
      )}

      {/* ========================================================================= */}
      {/* LAB 4: POS TAGGING & NER (CO3)                                           */}
      {/* ========================================================================= */}
      {activeLab === 'pos_ner' && (
        <div className="space-y-6">
          {!inspection && (
            <div className="glass-panel p-8 rounded-2xl border border-stone-200 text-center">
              <Layers className="w-8 h-8 text-emerald-700 mx-auto mb-2 opacity-80" />
              <h3 className="text-base font-serif font-bold text-stone-800">Execute Tagging Analysis</h3>
              <p className="text-xs text-stone-600 max-w-md mx-auto mt-1">
                Click <strong>Execute NLP Pipeline</strong> above to compare our from-scratch HMM Viterbi tagger against spaCy's neural POS model and inspect named entities.
              </p>
            </div>
          )}

          {inspection && (
            <div className="space-y-6">
              {/* POS Tagging Comparison Table (HMM Viterbi vs spaCy) */}
              <section className="lab-panel p-6 rounded-2xl border border-stone-200 bg-white">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <p className="eyebrow text-[10px] text-stone-500 font-mono">STATISTICAL VS NEURAL SEQUENCE LABELING</p>
                    <h3 className="font-serif font-bold text-lg text-stone-900">
                      HMM (Viterbi) vs spaCy POS Tagging Comparison
                    </h3>
                  </div>
                  {inspection.hmm_pos_tagging && (
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-mono text-stone-500 block">Viterbi Log-Likelihood</span>
                      <strong className="font-mono text-xs text-emerald-900">
                        {inspection.hmm_pos_tagging.log_likelihood}
                      </strong>
                    </div>
                  )}
                </div>

                <div className="table-scroll max-h-72 overflow-y-auto border border-stone-200 rounded-xl">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-stone-100 sticky top-0">
                      <tr>
                        <th className="p-2 border-b">Token</th>
                        <th className="p-2 border-b">HMM POS (Viterbi)</th>
                        <th className="p-2 border-b">spaCy Neural POS</th>
                        <th className="p-2 border-b text-center">Agreement</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inspection.hmm_pos_tagging?.pos_comparison.map((row, i) => (
                        <tr key={i} className="border-b border-stone-100 hover:bg-stone-50 font-mono text-[11px]">
                          <td className="p-2 font-bold text-stone-900">{row.token}</td>
                          <td className="p-2 text-indigo-950 font-semibold">{row.hmm_pos}</td>
                          <td className="p-2 text-emerald-950 font-semibold">{row.spacy_pos}</td>
                          <td className="p-2 text-center">
                            {row.match ? (
                              <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded text-[10px]">✓ Match</span>
                            ) : (
                              <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-[10px]">≠ Discrepancy</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-[11px] text-stone-500 mt-2 font-mono italic">
                  Algorithm: First-order Hidden Markov Model with Laplace smoothing & Viterbi dynamic programming trellis decoding.
                </p>
              </section>

              {/* Token Explorer with Dependencies & Head Tokens */}
              <section className="lab-panel p-6 rounded-2xl border border-stone-200 bg-white">
                <p className="eyebrow text-[10px] text-stone-500 font-mono">SYNTACTIC PARSER & DEPENDENCY TREE</p>
                <h3 className="font-serif font-bold text-lg text-stone-900 mb-1">Interactive Token Explorer</h3>
                <p className="text-xs text-stone-600 mb-3">Select any token to inspect its grammatical dependency relation, head token, and lemma.</p>

                <div className="token-cloud flex flex-wrap gap-2 mb-4">
                  {inspection.tokens.map((tok, i) => (
                    <button
                      key={i}
                      aria-pressed={tokenIndex === i}
                      className={`p-2 rounded-xl border text-left cursor-pointer transition ${
                        tokenIndex === i
                          ? 'border-emerald-800 bg-emerald-50 text-emerald-950'
                          : 'border-stone-200 bg-stone-50 hover:bg-stone-100 text-stone-800'
                      }`}
                      onClick={() => setTokenIndex(i)}
                    >
                      <strong className="block text-xs font-semibold">{tok.text}</strong>
                      <small className="block text-[10px] font-mono text-stone-500">{tok.pos}</small>
                    </button>
                  ))}
                </div>

                {selectedToken && (
                  <div className="p-4 bg-stone-50 rounded-xl border border-stone-200 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
                    <div>
                      <dt className="text-stone-500 text-[10px] uppercase">Lemma</dt>
                      <dd className="font-bold text-stone-900 text-sm">{selectedToken.lemma}</dd>
                    </div>
                    <div>
                      <dt className="text-stone-500 text-[10px] uppercase">POS & Detailed Tag</dt>
                      <dd className="font-bold text-stone-900 text-sm">{selectedToken.pos} ({selectedToken.tag || '—'})</dd>
                    </div>
                    <div>
                      <dt className="text-stone-500 text-[10px] uppercase">Dependency Relation</dt>
                      <dd className="font-bold text-emerald-800 text-sm">{selectedToken.dependency}</dd>
                    </div>
                    <div>
                      <dt className="text-stone-500 text-[10px] uppercase">Head Token</dt>
                      <dd className="font-bold text-stone-900 text-sm">"{selectedToken.head}"</dd>
                    </div>
                  </div>
                )}
              </section>

              {/* Named Entity Recognition (NER) Notebook */}
              <section className="lab-panel p-6 rounded-2xl border border-stone-200 bg-white">
                <p className="eyebrow text-[10px] text-stone-500 font-mono">NAMED ENTITY RECOGNITION (NER)</p>
                <h3 className="font-serif font-bold text-lg text-stone-900 mb-2">Entities & Noun Phrases</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <h4 className="font-semibold text-stone-700 mb-2">Detected Entities (PERSON, GPE, DATE, ORG)</h4>
                    {inspection.entities.length ? (
                      <div className="space-y-1.5">
                        {inspection.entities.map((ent, i) => (
                          <div key={i} className="flex justify-between items-center p-2 bg-stone-50 rounded-xl border border-stone-200 font-mono">
                            <strong className="text-stone-900">{ent.text}</strong>
                            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-900 rounded text-[10px] font-bold">
                              {ent.label}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-stone-400 italic">No named entities recognized in the input sentence.</p>
                    )}
                  </div>

                  <div>
                    <h4 className="font-semibold text-stone-700 mb-2">Noun Phrases (Chunks)</h4>
                    {inspection.noun_chunks.length ? (
                      <div className="flex flex-wrap gap-1.5">
                        {inspection.noun_chunks.map((nc, i) => (
                          <span key={i} className="px-2.5 py-1 bg-stone-100 border border-stone-200 rounded-lg font-mono text-[11px] text-stone-800">
                            {nc.text} (root: {nc.root})
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-stone-400 italic">No noun chunks recognized.</p>
                    )}
                  </div>
                </div>
              </section>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* LAB 5: MODEL TRAINING & EVALUATION (CO4)                                  */}
      {/* ========================================================================= */}
      {activeLab === 'models' && (
        <div className="space-y-6">
          {reportError && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-800 rounded-xl text-xs">
              {reportError}
            </div>
          )}

          {report && (
            <section className="lab-panel p-6 sm:p-8 rounded-2xl border border-stone-200 bg-white">
              <p className="eyebrow text-[10px] text-stone-500 font-mono">HELD-OUT BENCHMARK EVALUATION (CO4)</p>
              <h2 className="text-xl sm:text-2xl font-serif text-stone-900 font-bold mb-1">
                Comparative Classifier Performance
              </h2>
              <p className="text-xs sm:text-sm text-stone-600 mb-4">{report.task}.</p>

              {/* Data Split Stat Strip */}
              <div className="split-strip grid grid-cols-3 gap-4 p-4 bg-stone-50 rounded-xl border border-stone-200 mb-6 text-center">
                {Object.entries(report.split_sizes).map(([name, count]) => (
                  <div key={name}>
                    <span className="text-[10px] uppercase font-mono text-stone-500">{name} Split</span>
                    <strong className="text-xl sm:text-2xl font-serif text-stone-900 block mt-1">
                      {count.toLocaleString()}
                    </strong>
                  </div>
                ))}
              </div>

              {/* Model Comparison Table */}
              <div className="table-scroll border border-stone-200 rounded-xl overflow-x-auto mb-6">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-stone-100">
                    <tr>
                      <th className="p-3 border-b font-bold">Model Architecture</th>
                      <th className="p-3 border-b font-bold">Val Macro-F1</th>
                      <th className="p-3 border-b font-bold">Test Macro-F1</th>
                      <th className="p-3 border-b font-bold">Toxic Precision</th>
                      <th className="p-3 border-b font-bold">Toxic Recall</th>
                      <th className="p-3 border-b font-bold">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-stone-100 text-stone-500 font-mono">
                      <td className="p-3 font-semibold">Majority-Class Baseline</td>
                      <td className="p-3">—</td>
                      <td className="p-3">{report.majority_baseline.macro_f1.toFixed(3)}</td>
                      <td className="p-3">{percent(report.majority_baseline.per_class['toxic'].precision)}</td>
                      <td className="p-3">{percent(report.majority_baseline.per_class['toxic'].recall)}</td>
                      <td className="p-3">{percent(report.majority_baseline.accuracy)}</td>
                    </tr>
                    {Object.entries(report.models).map(([mName, scores]) => (
                      <tr
                        key={mName}
                        className={`border-b border-stone-100 font-mono ${
                          mName === report.selected_model ? 'bg-emerald-50/60 text-emerald-950 font-bold' : ''
                        }`}
                      >
                        <td className="p-3">
                          {displayName(mName)}
                          {mName === report.selected_model && (
                            <span className="ml-2 px-1.5 py-0.5 bg-emerald-800 text-white rounded text-[9px] font-sans">
                              SELECTED
                            </span>
                          )}
                        </td>
                        <td className="p-3">{scores.validation.macro_f1.toFixed(3)}</td>
                        <td className="p-3">{scores.test.macro_f1.toFixed(3)}</td>
                        <td className="p-3">{percent(scores.test.per_class['toxic'].precision)}</td>
                        <td className="p-3">{percent(scores.test.per_class['toxic'].recall)}</td>
                        <td className="p-3">{percent(scores.test.accuracy)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Selected Model 2x2 Confusion Grid */}
              <h3 className="font-serif font-bold text-base text-stone-900 mb-2">
                Held-Out Confusion Matrix ({displayName(report.selected_model)})
              </h3>
              <p className="text-xs text-stone-500 mb-3">Rows = True Label; Columns = Predicted Label.</p>

              <div className="confusion-grid grid grid-cols-2 gap-3 max-w-md">
                {report.models[report.selected_model].test.confusion_matrix.flatMap((row, i) =>
                  row.map((val, j) => (
                    <div
                      key={`${i}-${j}`}
                      className={`p-4 rounded-xl border text-center ${
                        i === j ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'
                      }`}
                    >
                      <span className="text-[10px] uppercase font-mono text-stone-500 block">
                        {i === 0 ? 'Not toxic' : 'Toxic'} ➔ {j === 0 ? 'Not toxic' : 'Toxic'}
                      </span>
                      <strong className="text-xl font-serif text-stone-900 block mt-1">
                        {val.toLocaleString()}
                      </strong>
                    </div>
                  ))
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-stone-200 text-xs text-stone-500">
                <a
                  className="source-link text-emerald-800 underline inline-flex items-center gap-1 font-semibold"
                  href={report.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  <span>Dataset: {report.dataset} (Revision: {report.dataset_revision})</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </section>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* LAB 6: HOSTED LLM INTEGRATION (CO5)                                       */}
      {/* ========================================================================= */}
      {activeLab === 'hosted' && (
        <div className="space-y-6">
          <section className="lab-panel p-6 sm:p-8 rounded-2xl border border-stone-200 bg-white">
            <p className="eyebrow text-[10px] text-stone-500 font-mono">INDEPENDENT GENERATIVE PERSPECTIVE (CO5)</p>
            <h2 className="text-xl sm:text-2xl font-serif text-stone-900 font-bold mb-1">
              Hosted LLM Second Opinion
            </h2>
            <p className="text-xs sm:text-sm text-stone-600 mb-4">
              Sends the conversation to a configured external language model via Hugging Face Inference Providers. Strict JSON schema parsing and exact-quote verification guarantee transparent evidence citation.
            </p>

            {hosted?.configured ? (
              <div className="space-y-4">
                <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 text-xs text-stone-600">
                  <span>Provider: <strong>{hosted.provider}</strong></span>
                  <span className="mx-2">•</span>
                  <span>Model: <strong>{hosted.model}</strong></span>
                </div>

                <label className="consent-checkbox flex items-start gap-2.5 text-xs text-stone-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={consent}
                    className="mt-0.5 accent-emerald-800"
                    onChange={(e) => setConsent(e.target.checked)}
                  />
                  <span>
                    I explicitly consent to send the transcript above to Hugging Face and its inference provider. Local privacy mode is bypassed only for this specific request.
                  </span>
                </label>

                <button
                  className="primary-action px-5 py-2.5 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded-xl flex items-center gap-2 cursor-pointer disabled:opacity-50"
                  disabled={!consent || busy || !text.trim() || text.length > 12000}
                  onClick={runSecondOpinion}
                >
                  {busy ? 'Requesting Review from Provider...' : 'Send for Hosted LLM Review'}
                  <ArrowRight size={14} />
                </button>
              </div>
            ) : (
              <div className="p-5 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-2">
                <div className="flex items-center gap-2 font-bold">
                  <AlertCircle size={16} />
                  <span>Hosted LLM Review is not yet configured</span>
                </div>
                <p>
                  To enable live LLM second opinions, configure <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">HF_TOKEN</code> and <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">HF_CHAT_MODEL</code> in the backend <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">.env</code> file.
                </p>
                <p className="text-[11px] text-amber-800">
                  All local NLP capabilities (CO1 preprocessing, CO2 vectorization & Word2Vec, CO3 HMM/Viterbi POS & NER, and CO4 local classification) run 100% locally on CPU without an external API key.
                </p>
              </div>
            )}

            {hostedResult && (
              <div className="hosted-result mt-6 pt-6 border-t border-stone-200 space-y-4 text-xs">
                <div className="flex items-center justify-between">
                  <span className="px-3 py-1 bg-emerald-100 text-emerald-900 font-bold rounded-lg uppercase tracking-wider text-[11px]">
                    Risk Assessment: {hostedResult.risk}
                  </span>
                  <span className="text-stone-400 font-mono text-[10px]">
                    Model: {hostedResult.model}
                  </span>
                </div>

                <div>
                  <h4 className="font-bold text-stone-800 mb-1">Executive Summary:</h4>
                  <p className="text-stone-700 bg-stone-50 p-3 rounded-xl border border-stone-200 leading-relaxed">
                    {hostedResult.summary}
                  </p>
                </div>

                <div>
                  <h4 className="font-bold text-stone-800 mb-1">Quoted Verifiable Evidence:</h4>
                  <div className="space-y-2">
                    {hostedResult.evidence.map((ev, i) => (
                      <blockquote key={i} className="p-3 bg-stone-50 border-l-4 border-emerald-700 rounded-r-xl">
                        <strong className="block text-stone-900">"{ev.quote}"</strong>
                        <p className="text-stone-600 mt-1">{ev.explanation}</p>
                      </blockquote>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-bold text-stone-800 mb-1">Alternative Interpretation:</h4>
                  <p className="text-stone-600 italic bg-stone-50 p-3 rounded-xl border border-stone-200">
                    {hostedResult.alternative_interpretation}
                  </p>
                </div>

                <div>
                  <h4 className="font-bold text-stone-800 mb-1">Suggested Intervention:</h4>
                  <p className="text-stone-700 bg-stone-50 p-3 rounded-xl border border-stone-200">
                    {hostedResult.suggested_action}
                  </p>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </section>
  );
}

export default NlpWorkbench;
