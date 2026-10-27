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
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/30 text-violet-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white">
              Scientific Methodology & Explainability Framework
            </h2>
            <p className="text-xs sm:text-sm text-slate-400">
              How ContextGuard combines multi-turn conversational NLP, sarcasm calibration, and ethical decision-support principles.
            </p>
          </div>
        </div>
      </div>

      {/* Grid of Core Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Pillar 1: Why Keyword Detectors Fail */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center space-x-2.5 text-teal-400 mb-3">
            <Layers className="w-5 h-5" />
            <h3 className="text-base font-bold text-white">1. Beyond Isolated Keyword Filtering</h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
            Legacy cyberbullying detectors use isolated token classification. A message like <code className="text-teal-300 font-mono bg-slate-900 px-1 py-0.5 rounded">"You're such an idiot 😂"</code> is flagged as severe toxicity, even when exchanged between long-time gaming friends in reciprocal humor.
          </p>
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 space-y-2">
            <div className="font-semibold text-slate-200">ContextGuard Context Anchors:</div>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li><strong>Laughter & Emoji Reciprocity:</strong> Mutual laughter across interlocutors suppresses false positives on friendly teasing.</li>
              <li><strong>Prior Relationship Context:</strong> Adjusts Bayesian priors based on declared peer dynamics (e.g. "Close Friends" vs "Anonymous Forum").</li>
              <li><strong>Interlocutor Reaction Tracking:</strong> Looks ahead to observe whether the recipient laughed, escalated playfully, or objected.</li>
            </ul>
          </div>
        </div>

        {/* Pillar 2: Sarcasm & The Intent Boundary */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center space-x-2.5 text-violet-400 mb-3">
            <HelpCircle className="w-5 h-5" />
            <h3 className="text-base font-bold text-white">2. Sarcasm Calibration & Incomplete Context</h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
            Sarcasm involves sentiment inversion (e.g., <code className="text-violet-300 font-mono bg-slate-900 px-1 py-0.5 rounded">"Wow, you're a real genius."</code>). Sarcasm alone does NOT prove cyberbullying.
          </p>
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 space-y-2">
            <div className="font-semibold text-slate-200">Preserving Uncertainty:</div>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li><strong>When context is brief or ambiguous:</strong> ContextGuard marks the turn as <span className="text-slate-300 font-semibold font-mono">Uncertain — More Context Needed</span> rather than forcing a false accusation.</li>
              <li><strong>When distress follows:</strong> If the recipient asks <span className="italic">"What is that supposed to mean?"</span>, the confidence of negative impact increases.</li>
            </ul>
          </div>
        </div>

        {/* Pillar 3: Repeated Targeting & Power Asymmetry */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center space-x-2.5 text-orange-400 mb-3">
            <ShieldAlert className="w-5 h-5" />
            <h3 className="text-base font-bold text-white">3. Repeated Targeting & Systematic Exclusion</h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
            Cyberbullying is academically defined by repetition and power imbalance (Olweus, 1993; Hinduja & Patchin, 2014). An isolated harsh statement differs fundamentally from sustained ostracism.
          </p>
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 space-y-2">
            <div className="font-semibold text-slate-200">Asymmetry Metrics:</div>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li>Counts directional hostile turns (<span className="text-orange-400 font-mono">Source ➔ Target</span>).</li>
              <li>Flags unreciprocated exclusionary patterns (<span className="italic">"Nobody wants you in this group"</span>).</li>
              <li>Distinguishes bilateral arguments from unilateral targeted piling-on.</li>
            </ul>
          </div>
        </div>

        {/* Pillar 4: Model Transparency & Honest Scoring */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center space-x-2.5 text-cyan-400 mb-3">
            <Cpu className="w-5 h-5" />
            <h3 className="text-base font-bold text-white">4. Honest Scoring vs Pseudo-Probabilities</h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
            Many AI apps output uncalibrated "98% Toxic" numbers that mislead users into thinking machine learning has "read someone's soul."
          </p>
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 space-y-2">
            <div className="font-semibold text-slate-200">ContextGuard Transparency Standard:</div>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li><strong>Risk Scores are Estimates:</strong> Expressed as index metrics (0-100), not absolute truths.</li>
              <li><strong>Model vs Heuristics:</strong> We explicitly distinguish transformer neural logits from contextual conversational heuristics.</li>
              <li><strong>Never Automatic Sanctions:</strong> Strictly designed for human moderation assistance, never automated punishment.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* College Viva & Architecture Presentation Card */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 bg-slate-900/40">
        <div className="flex items-center space-x-2 text-teal-400 mb-4">
          <GraduationCap className="w-5 h-5" />
          <h3 className="text-lg font-bold text-white">
            Academic Viva & Project Demonstration Notes
          </h3>
        </div>

        <div className="space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
          <p>
            When demonstrating ContextGuard in an academic evaluation or viva presentation, emphasize these core design decisions:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-teal-400 font-bold block mb-1">Architecture</span>
              <span className="text-slate-400 font-sans">
                FastAPI backend with modular services (<code className="text-teal-300">parser.py</code>, <code className="text-teal-300">features.py</code>, <code className="text-teal-300">engine.py</code>) enabling drop-in fine-tuned RoBERTa/DeBERTa checkpoints.
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-indigo-400 font-bold block mb-1">Taxonomy</span>
              <span className="text-slate-400 font-sans">
                6 calibrated categories from Friendly Banter to Urgent Threat, based on Davidson et al. (Hate Speech vs Offensive Language) and Waseem et al.
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-cyan-400 font-bold block mb-1">Privacy Standard</span>
              <span className="text-slate-400 font-sans">
                Deterministic local analysis with zero external logging of conversations, compliant with COPPA and EU AI Act high-risk assistive system safeguards.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
