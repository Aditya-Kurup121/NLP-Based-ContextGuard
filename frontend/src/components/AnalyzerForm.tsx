import React, { useState } from 'react';
import { Play, RotateCcw, HelpCircle, Sliders, AlertCircle } from 'lucide-react';
import type { ExampleConversation, ContextInfo } from '../types';

interface AnalyzerFormProps {
  conversationText: string;
  setConversationText: (text: string) => void;
  contextInfo: ContextInfo;
  setContextInfo: React.Dispatch<React.SetStateAction<ContextInfo>>;
  examples: ExampleConversation[];
  onSelectExample: (example: ExampleConversation) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  onClear: () => void;
  error: string | null;
}

export const AnalyzerForm: React.FC<AnalyzerFormProps> = ({
  conversationText,
  setConversationText,
  contextInfo,
  setContextInfo,
  examples,
  onSelectExample,
  onAnalyze,
  isLoading,
  onClear,
  error,
}) => {
  const [showAdvancedContext, setShowAdvancedContext] = useState(false);

  // Compute live turn count
  const estimatedTurns = conversationText
    .split('\n')
    .filter(line => line.trim().length > 0)
    .length;

  return (
    <div id="analyzer-form-section" className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-2xl relative">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center space-x-2">
            <span>Conversation Input & Context</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20 font-mono">
              Multi-Turn
            </span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Paste chronological chat turns formatted as <code className="text-teal-300 font-mono bg-slate-900 px-1 py-0.5 rounded">Speaker: Message</code> or select a preloaded sample.
          </p>
        </div>

        {/* Quick Sample Selector Dropdown */}
        <div className="w-full md:w-auto flex items-center space-x-2">
          <label htmlFor="sample-selector" className="text-xs text-slate-400 whitespace-nowrap">Load Preset:</label>
          <select
            id="sample-selector"
            onChange={(e) => {
              const selected = examples.find(ex => ex.id === e.target.value);
              if (selected) onSelectExample(selected);
            }}
            defaultValue=""
            className="w-full md:w-64 text-xs bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          >
            <option value="" disabled>-- Select a Demonstration Case --</option>
            {examples.map(ex => (
              <option key={ex.id} value={ex.id}>
                {ex.title} ({ex.category})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Preset Pills for One-Click Testing */}
      <div className="mb-4 flex flex-wrap gap-2">
        <span className="text-xs font-medium text-slate-400 self-center mr-1">Quick Scenarios:</span>
        {examples.slice(0, 4).map((ex) => (
          <button
            key={ex.id}
            onClick={() => onSelectExample(ex)}
            className="text-xs px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 transition-colors cursor-pointer"
          >
            {ex.id === 'friendly-banter' && '😂 Friendly Banter'}
            {ex.id === 'repeated-exclusion' && '🚫 Repeated Exclusion'}
            {ex.id === 'sarcasm-ambiguity' && '🎭 Sarcasm & Ambiguity'}
            {ex.id === 'threatening-language' && '⚠️ Physical Threat'}
          </button>
        ))}
      </div>

      {/* Main Textarea */}
      <div className="relative mb-4">
        <textarea
          id="conversation-input"
          value={conversationText}
          onChange={(e) => setConversationText(e.target.value)}
          placeholder={`Alice: You're such a genius 😂\nBob: Bro, I know. Nobel Prize incoming.\nAlice: Don't forget us when you're famous.`}
          rows={7}
          className="w-full bg-slate-950/80 border border-slate-800 rounded-xl p-4 font-mono text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-all resize-y"
        />

        {/* Floating status counters */}
        <div className="absolute bottom-3 right-3 flex items-center space-x-3 text-xs font-mono text-slate-400 bg-slate-900/90 px-2.5 py-1 rounded-md border border-slate-800">
          <span>{conversationText.length} chars</span>
          <span className="text-slate-600">•</span>
          <span className={estimatedTurns > 0 ? 'text-teal-300 font-semibold' : 'text-slate-500'}>
            {estimatedTurns} turn{estimatedTurns === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {/* Advanced Context Drawer Toggle */}
      <div className="mb-6">
        <button
          type="button"
          onClick={() => setShowAdvancedContext(!showAdvancedContext)}
          className="flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-teal-300 transition-colors"
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>{showAdvancedContext ? 'Hide' : 'Add'} Conversational Context (Relationship, Setting, Background)</span>
          <span className="text-slate-600">({contextInfo.relationship || 'Unspecified'})</span>
        </button>

        {showAdvancedContext && (
          <div className="mt-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 animate-in fade-in duration-200">
            <div>
              <label htmlFor="context-relationship" className="block text-xs font-medium text-slate-300 mb-1">
                Participant Relationship
              </label>
              <input
                id="context-relationship"
                type="text"
                value={contextInfo.relationship}
                onChange={(e) => setContextInfo(prev => ({ ...prev, relationship: e.target.value }))}
                placeholder="e.g. Close friends, Classmates, Strangers"
                className="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500"
              />
            </div>

            <div>
              <label htmlFor="context-setting" className="block text-xs font-medium text-slate-300 mb-1">
                Platform / Setting
              </label>
              <input
                id="context-setting"
                type="text"
                value={contextInfo.setting}
                onChange={(e) => setContextInfo(prev => ({ ...prev, setting: e.target.value }))}
                placeholder="e.g. Group chat, Direct message, Public forum"
                className="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500"
              />
            </div>

            <div>
              <label htmlFor="context-notes" className="block text-xs font-medium text-slate-300 mb-1">
                Background / History (Optional)
              </label>
              <input
                id="context-notes"
                type="text"
                value={contextInfo.additional_information || ''}
                onChange={(e) => setContextInfo(prev => ({ ...prev, additional_information: e.target.value }))}
                placeholder="e.g. Frequent sarcasm, Recent argument"
                className="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start space-x-3 text-red-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold block">Input Validation Error</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <HelpCircle className="w-4 h-4 text-slate-500" />
          <span>Expected format: Each message starts with speaker name and colon.</span>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <button
            type="button"
            onClick={onClear}
            disabled={isLoading || (!conversationText && !contextInfo.additional_information)}
            className="flex-1 sm:flex-none flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-900 hover:bg-slate-800 border border-slate-800 transition-colors disabled:opacity-50 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear Input</span>
          </button>

          <button
            type="button"
            id="analyze-conversation-btn"
            onClick={onAnalyze}
            disabled={isLoading || !conversationText.trim()}
            className="flex-1 sm:flex-none flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 shadow-lg shadow-teal-500/20 hover:shadow-teal-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Analyzing Context Dynamics...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Analyze Conversation</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
