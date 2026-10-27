import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingHero } from './components/LandingHero';
import { AnalyzerForm } from './components/AnalyzerForm';
import { RiskSummaryCard } from './components/RiskSummaryCard';
import { ConversationTimeline } from './components/ConversationTimeline';
import { MessageDetailModal } from './components/MessageDetailModal';
import { InteractionMatrix } from './components/InteractionMatrix';
import { MethodologySection } from './components/MethodologySection';
import { BenchmarkSection } from './components/BenchmarkSection';

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
  const [activeTab, setActiveTab] = useState<'analyzer' | 'network' | 'methodology' | 'benchmark'>('analyzer');
  const [backendOnline, setBackendOnline] = useState<boolean>(true);
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
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500/30 selection:text-teal-200">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendOnline={backendOnline}
        onClearAll={handleClearAll}
        hasResults={Boolean(analysisResult)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        {/* Tab 1: Analyzer */}
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
                {/* Result Action Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl glass-panel border border-slate-800">
                  <div className="flex items-center space-x-2 text-xs text-slate-400">
                    <Sparkles className="w-4 h-4 text-teal-400" />
                    <span>Analysis generated via <strong className="text-slate-200 font-mono">{analysisResult.model_info.engine_name}</strong></span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => window.print()}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 transition-colors cursor-pointer"
                      title="Print or save as PDF report"
                    >
                      <Printer className="w-3.5 h-3.5" />
                      <span>Export / Print</span>
                    </button>

                    <button
                      onClick={() => setActiveTab('network')}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-300 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 transition-colors cursor-pointer"
                    >
                      <span>View Interaction Matrix</span>
                    </button>
                  </div>
                </div>

                {/* Risk Summary Card */}
                <RiskSummaryCard results={analysisResult} />

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
            <InteractionMatrix
              participants={analysisResult.participants}
              targetingPatterns={analysisResult.targeting_patterns}
              messages={analysisResult.messages}
            />
          ) : (
            <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800 max-w-xl mx-auto my-12">
              <Sparkles className="w-10 h-10 text-indigo-400 mx-auto mb-4" />
              <h3 className="text-lg font-bold text-white mb-2">No Active Conversation Analyzed</h3>
              <p className="text-xs text-slate-400 mb-6">
                Analyze a conversation first to map participant interaction patterns, directed hostile turns, and targeting asymmetry.
              </p>
              <button
                onClick={() => {
                  if (examples.length > 0) {
                    handleSelectExample(examples[1] || examples[0]);
                  }
                  setActiveTab('analyzer');
                }}
                className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-indigo-500 to-teal-500 hover:from-indigo-400 hover:to-teal-400 shadow-md transition-all cursor-pointer"
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
      <footer className="glass-panel border-t border-slate-800/80 py-8 mt-12 bg-navy-950/90 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-teal-400" />
            <span className="font-semibold text-slate-200">ContextGuard</span>
            <span>— Assistive Conversational NLP for Cyberbullying Detection</span>
          </div>

          <div className="flex items-center space-x-6 text-slate-500">
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
