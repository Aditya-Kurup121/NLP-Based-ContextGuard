import React from 'react';
import { 
  BookOpen, 
  Layers, 
  HelpCircle, 
  ShieldAlert, 
  Cpu, 
  GraduationCap
} from 'lucide-react';

export const MethodologySection: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-stone-200 shadow-sm">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/30 text-stone-600">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-stone-900">
              Scientific Methodology & Explainability Framework
            </h2>
            <p className="text-xs sm:text-sm text-stone-600">
              How ContextGuard combines multi-turn conversational NLP, sarcasm calibration, and ethical decision-support principles.
            </p>
          </div>
        </div>
      </div>

      {/* Grid of Core Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Pillar 1: Why Keyword Detectors Fail */}
        <div className="glass-panel rounded-2xl p-6 border border-stone-200">
          <div className="flex items-center space-x-2.5 text-emerald-700 mb-3">
            <Layers className="w-5 h-5" />
            <h3 className="text-base font-bold text-stone-900">1. Beyond Isolated Keyword Filtering</h3>
          </div>
          <p className="text-xs sm:text-sm text-stone-700 leading-relaxed mb-4">
            Legacy cyberbullying detectors use isolated token classification. A message like <code className="text-emerald-800 font-mono bg-stone-100 px-1 py-0.5 rounded">"You're such an idiot 😂"</code> is flagged as severe toxicity, even when exchanged between long-time gaming friends in reciprocal humor.
          </p>
          <div className="p-3.5 rounded-xl bg-stone-100/60 border border-stone-200 text-xs text-stone-700 space-y-2">
            <div className="font-semibold text-stone-800">ContextGuard Context Anchors:</div>
            <ul className="list-disc list-inside space-y-1 text-stone-600">
              <li><strong>Laughter & Emoji Reciprocity:</strong> Mutual laughter across interlocutors suppresses false positives on friendly teasing.</li>
              <li><strong>Prior Relationship Context:</strong> Adjusts contextual rules based on declared peer dynamics (e.g. "Close Friends" vs "Anonymous Forum").</li>
              <li><strong>Interlocutor Reaction Tracking:</strong> Looks ahead to observe whether the recipient laughed, escalated playfully, or objected.</li>
            </ul>
          </div>
        </div>

        {/* Pillar 2: Sarcasm & The Intent Boundary */}
        <div className="glass-panel rounded-2xl p-6 border border-stone-200">
          <div className="flex items-center space-x-2.5 text-stone-600 mb-3">
            <HelpCircle className="w-5 h-5" />
            <h3 className="text-base font-bold text-stone-900">2. Sarcasm Calibration & Incomplete Context</h3>
          </div>
          <p className="text-xs sm:text-sm text-stone-700 leading-relaxed mb-4">
            Sarcasm involves sentiment inversion (e.g., <code className="text-stone-700 font-mono bg-stone-100 px-1 py-0.5 rounded">"Wow, you're a real genius."</code>). Sarcasm alone does NOT prove cyberbullying.
          </p>
          <div className="p-3.5 rounded-xl bg-stone-100/60 border border-stone-200 text-xs text-stone-700 space-y-2">
            <div className="font-semibold text-stone-800">Preserving Uncertainty:</div>
            <ul className="list-disc list-inside space-y-1 text-stone-600">
              <li><strong>When context is brief or ambiguous:</strong> ContextGuard marks the turn as <span className="text-stone-700 font-semibold font-mono">Uncertain — More Context Needed</span> rather than forcing a false accusation.</li>
              <li><strong>When distress follows:</strong> If the recipient asks <span className="italic">"What is that supposed to mean?"</span>, the confidence of negative impact increases.</li>
            </ul>
          </div>
        </div>

        {/* Pillar 3: Repeated Targeting & Power Asymmetry */}
        <div className="glass-panel rounded-2xl p-6 border border-stone-200">
          <div className="flex items-center space-x-2.5 text-orange-700 mb-3">
            <ShieldAlert className="w-5 h-5" />
            <h3 className="text-base font-bold text-stone-900">3. Repeated Targeting & Systematic Exclusion</h3>
          </div>
          <p className="text-xs sm:text-sm text-stone-700 leading-relaxed mb-4">
            Cyberbullying is academically defined by repetition and power imbalance (Olweus, 1993; Hinduja & Patchin, 2014). An isolated harsh statement differs fundamentally from sustained ostracism.
          </p>
          <div className="p-3.5 rounded-xl bg-stone-100/60 border border-stone-200 text-xs text-stone-700 space-y-2">
            <div className="font-semibold text-stone-800">Asymmetry Metrics:</div>
            <ul className="list-disc list-inside space-y-1 text-stone-600">
              <li>Counts directional hostile turns (<span className="text-orange-700 font-mono">Source ➔ Target</span>).</li>
              <li>Flags unreciprocated exclusionary patterns (<span className="italic">"Nobody wants you in this group"</span>).</li>
              <li>Distinguishes bilateral arguments from unilateral targeted piling-on.</li>
            </ul>
          </div>
        </div>

        {/* Pillar 4: Model Transparency & Honest Scoring */}
        <div className="glass-panel rounded-2xl p-6 border border-stone-200">
          <div className="flex items-center space-x-2.5 text-emerald-700 mb-3">
            <Cpu className="w-5 h-5" />
            <h3 className="text-base font-bold text-stone-900">4. Honest Scoring vs Pseudo-Probabilities</h3>
          </div>
          <p className="text-xs sm:text-sm text-stone-700 leading-relaxed mb-4">
            Many AI apps output uncalibrated "98% Toxic" numbers that mislead users into thinking machine learning has "read someone's soul."
          </p>
          <div className="p-3.5 rounded-xl bg-stone-100/60 border border-stone-200 text-xs text-stone-700 space-y-2">
            <div className="font-semibold text-stone-800">ContextGuard Transparency Standard:</div>
            <ul className="list-disc list-inside space-y-1 text-stone-600">
              <li><strong>Risk Scores are Estimates:</strong> Expressed as index metrics (0-100), not absolute truths.</li>
              <li><strong>Model vs Heuristics:</strong> The current engine uses contextual rules. Its scores are heuristic estimates, not trained model probabilities.</li>
              <li><strong>Never Automatic Sanctions:</strong> Strictly designed for human moderation assistance, never automated punishment.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* College Viva & Architecture Presentation Card */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-stone-200 bg-stone-100/40">
        <div className="flex items-center space-x-2 text-emerald-700 mb-4">
          <GraduationCap className="w-5 h-5" />
          <h3 className="text-lg font-bold text-stone-900">
            Academic Viva & Project Demonstration Notes
          </h3>
        </div>

        <div className="space-y-4 text-xs sm:text-sm text-stone-700 leading-relaxed">
          <p>
            When demonstrating ContextGuard in an academic evaluation or viva presentation, emphasize these core design decisions:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-3 rounded-xl bg-stone-50 border border-stone-200">
              <span className="text-emerald-700 font-bold block mb-1">Architecture</span>
              <span className="text-stone-600 font-sans">
                FastAPI backend with modular services (<code className="text-emerald-800">parser.py</code>, <code className="text-emerald-800">features.py</code>, <code className="text-emerald-800">engine.py</code>) with separate parsing, feature extraction, and rule-based classification stages.
              </span>
            </div>

            <div className="p-3 rounded-xl bg-stone-50 border border-stone-200">
              <span className="text-emerald-700 font-bold block mb-1">Taxonomy</span>
              <span className="text-stone-600 font-sans">
                6 rule-assigned categories from Friendly Banter to Urgent Threat. The trained comment classifier is reported as a separate signal.
              </span>
            </div>

            <div className="p-3 rounded-xl bg-stone-50 border border-stone-200">
              <span className="text-emerald-700 font-bold block mb-1">Privacy Standard</span>
              <span className="text-stone-600 font-sans">
                Conversation analysis runs on the configured backend. No persistent conversation database is implemented.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

