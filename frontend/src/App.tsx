import React, { useState, useEffect, lazy, Suspense } from 'react';
import { Navbar } from './components/Navbar';
import { LandingHero } from './components/LandingHero';
import { AnalyzerForm } from './components/AnalyzerForm';
import { RiskSummaryCard } from './components/RiskSummaryCard';
import { ConversationTimeline } from './components/ConversationTimeline';
import { MessageDetailModal } from './components/MessageDetailModal';
const InteractionMatrix = lazy(() => import('./components/InteractionMatrix').then(m => ({ default: m.InteractionMatrix })));
import { MethodologySection } from './components/MethodologySection';
import { BenchmarkSection } from './components/BenchmarkSection';
import { ConversationPulse } from './components/ConversationPulse';
const NlpWorkbench = lazy(() => import('./components/NlpWorkbench').then(m => ({ default: m.NlpWorkbench })));
const WhatsAppImport = lazy(() => import('./components/WhatsAppImport').then(m => ({ default: m.WhatsAppImport })));

import type { 
  ExampleConversation, 
  ContextInfo, 
  AnalyzeResponse, 
  MessageAnalysis 
} from './types';
import { 
  checkBackendHealth, 
  fetchExamples, 
  analyzeConversation 
} from './services/api';
import { 
  ShieldCheck, 
  Sparkles, 
  Printer 
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'analyzer' | 'network' | 'methodology' | 'benchmark' | 'lab' | 'import'>('analyzer');
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [importVisited, setImportVisited] = useState(false);
  const [examples, setExamples] = useState<ExampleConversation[]>([]);
  
  // Input form state
  const [conversationText, setConversationText] = useState<string>('');
  const [contextInfo, setContextInfo] = useState<ContextInfo>({
    relationship: 'Unspecified',
    setting: 'Group chat',
    additional_information: ''
  });

  // Analysis result state
  const [analysisResult, setAnalysisResult] = useState<AnalyzeResponse | null>(null);
  const [reviewedInput, setReviewedInput] = useState('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<MessageAnalysis | null>(null);

  // Initialize and check backend
  useEffect(() => {
    async function init() {
      try {
        await checkBackendHealth();
        setBackendOnline(true);
      } catch (e) {
        console.warn('Backend not responding yet:', e);
        setBackendOnline(false);
      }

      try {
        const loadedExamples = await fetchExamples();
        setExamples(loadedExamples);
      } catch (e) {
        console.warn('Could not fetch examples from backend:', e);
      }
    }
    init();
  }, []);

  // Handle Preset Load
  const handleSelectExample = (ex: ExampleConversation) => {
    setConversationText(ex.conversation);
    setContextInfo({
      relationship: ex.relationship,
      setting: ex.setting,
      additional_information: ex.description
    });
    setError(null);
    setActiveTab('analyzer');

    // Auto-scroll to form
    const elem = document.getElementById('analyzer-form-section');
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Run Analysis
  const handleAnalyze = async () => {
    if (!conversationText.trim()) {
      setError('Please provide at least one conversation turn.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await analyzeConversation({
        conversation: conversationText,
        context: contextInfo
      });
      setAnalysisResult(response);
      setReviewedInput(JSON.stringify([conversationText, contextInfo]));

      // Scroll smoothly to results
      setTimeout(() => {
        const resultsEl = document.getElementById('results-anchor');
        if (resultsEl) {
          resultsEl.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    } catch (err: any) {
      setError(err.message || 'Analysis failed. Please check backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // Clear All Data
  const handleClearAll = () => {
    setConversationText('');
    setContextInfo({
      relationship: 'Unspecified',
      setting: 'Group chat',
      additional_information: ''
    });
    setAnalysisResult(null);
    setError(null);
    setSelectedMessage(null);
  };

  return (
    <div className="app-shell min-h-screen flex flex-col font-sans">
      <a className="skip-link" href="#main-content">Skip to workspace</a>
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={tab => { if (tab === 'import') setImportVisited(true); setActiveTab(tab); }}
        backendOnline={backendOnline}
        onClearAll={handleClearAll}
        hasResults={Boolean(analysisResult) && activeTab !== 'import'}
      />

      {/* Main Content Area */}
      <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        {/* Tab 1: Analyzer */}
        <div hidden={activeTab !== 'import'}><Suspense fallback={<p role="status">Opening the import workspace…</p>}>{importVisited && <WhatsAppImport />}</Suspense></div>
        {activeTab === 'analyzer' && (
          <>
            {/* Show landing hero if no analysis yet */}
            {!analysisResult && (
              <LandingHero
                onStartAnalysis={() => {
                  const el = document.getElementById('analyzer-form-section');
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }}
                onLoadSample={(sampleId) => {
                  const ex = examples.find(e => e.id === sampleId);
                  if (ex) handleSelectExample(ex);
                  else setError('Sample conversations are unavailable. Start the local backend to load them, or paste your own conversation.');
                }}
              />
            )}

            {/* Form Section */}
            <AnalyzerForm
              conversationText={conversationText}
              setConversationText={setConversationText}
              contextInfo={contextInfo}
              setContextInfo={setContextInfo}
              examples={examples}
              onSelectExample={handleSelectExample}
              onAnalyze={handleAnalyze}
              isLoading={isLoading}
              onClear={handleClearAll}
              error={error}
            />

            {/* Results Section */}
            {analysisResult && (
              <div id="results-anchor" className="space-y-6 pt-4 animate-in fade-in duration-300">
                {reviewedInput !== JSON.stringify([conversationText, contextInfo]) && <div className="editor-error" role="status">The conversation or context has changed. These results belong to the previous review. Run a new review to update them.</div>}
                {/* Result Action Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl glass-panel border border-stone-200">
                  <div className="flex items-center space-x-2 text-xs text-stone-600">
                    <Sparkles className="w-4 h-4 text-emerald-700" />
                    <span>Analysis generated via <strong className="text-stone-800 font-mono">{analysisResult.model_info.engine_name}</strong></span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => window.print()}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-stone-700 hover:text-stone-900 bg-stone-100 hover:bg-stone-200 border border-stone-200 transition-colors cursor-pointer"
                      title="Print or save as PDF report"
                    >
                      <Printer className="w-3.5 h-3.5" />
                      <span>Export / Print</span>
                    </button>

                    <button
                      onClick={() => setActiveTab('network')}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-emerald-800 hover:text-stone-900 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 transition-colors cursor-pointer"
                    >
                      <span>View Interaction Matrix</span>
                    </button>
                  </div>
                </div>

                {/* Risk Summary Card */}
                <RiskSummaryCard results={analysisResult} />
                <ConversationPulse messages={analysisResult.messages} onSelect={setSelectedMessage} />

                {/* Interactive Message Timeline */}
                <ConversationTimeline
                  messages={analysisResult.messages}
                  onSelectMessage={(msg) => setSelectedMessage(msg)}
                />
              </div>
            )}
          </>
        )}

        {/* Tab 2: Interaction Network & Targeting Matrix */}
        {activeTab === 'network' && (
          analysisResult ? (
            <Suspense fallback={<p role="status">Loading interaction map…</p>}><InteractionMatrix
              participants={analysisResult.participants}
              targetingPatterns={analysisResult.targeting_patterns}
              messages={analysisResult.messages}
            /></Suspense>
          ) : (
            <div className="glass-panel rounded-2xl p-12 text-center border border-stone-200 max-w-xl mx-auto my-12">
              <Sparkles className="w-10 h-10 text-emerald-700 mx-auto mb-4" />
              <h3 className="text-lg font-bold text-stone-900 mb-2">No Active Conversation Analyzed</h3>
              <p className="text-xs text-stone-600 mb-6">
                Analyze a conversation first to map participant interaction patterns, directed hostile turns, and targeting asymmetry.
              </p>
              <button
                onClick={() => {
                  if (examples.length > 0) {
                    handleSelectExample(examples[1] || examples[0]);
                  }
                  setActiveTab('analyzer');
                }}
                className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-emerald-800     shadow-md transition-all cursor-pointer"
              >
                Load Sample & View Matrix
              </button>
            </div>
          )
        )}

        {/* Tab 3: Methodology & Research Viva */}
        {activeTab === 'methodology' && (
          <MethodologySection />
        )}

        {/* Tab 4: Benchmark Evaluation */}
        {activeTab === 'lab' && <Suspense fallback={<p role="status">Opening the language lab…</p>}><NlpWorkbench conversation={conversationText} /></Suspense>}
        {activeTab === 'benchmark' && (
          <BenchmarkSection />
        )}
      </main>

      {/* Message Explainability Modal */}
      <MessageDetailModal
        message={selectedMessage}
        onClose={() => setSelectedMessage(null)}
      />

      {/* Footer */}
      <footer className="glass-panel border-t border-stone-200/80 py-8 mt-12 bg-stone-50/90 text-xs text-stone-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700" />
            <span className="font-semibold text-stone-800">ContextGuard</span>
            <span>— Assistive Conversational NLP for Cyberbullying Detection</span>
          </div>

          <div className="flex items-center space-x-6 text-stone-500">
            <span>Decision-Support AI</span>
            <span>•</span>
            <span>Zero Persistent PII Storage</span>
            <span>•</span>
            <span>Modular NLP Architecture</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
