import React from 'react';
import { Layers, MessageSquareDashed, Users, ShieldCheck, ArrowRight, Eye, Sparkles } from 'lucide-react';

interface LandingHeroProps {
  onStartAnalysis: () => void;
  onLoadSample: (sampleId: string) => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({ onStartAnalysis, onLoadSample }) => {
  return (
    <section className="relative overflow-hidden pt-8 pb-12 sm:pt-12 sm:pb-16 border-b border-slate-800/80">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 text-center">
        {/* Subtle pill tag */}
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-slate-800/80 text-teal-300 border border-teal-500/30 mb-6 backdrop-blur-sm">
          <Sparkles className="w-3.5 h-3.5 text-teal-400" />
          <span>Decision-Support NLP • Explainable Conversational AI</span>
        </div>

        {/* Hero Heading */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white mb-6 leading-tight">
          Not every insult tells the <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-teal-300 via-cyan-200 to-indigo-400 bg-clip-text text-transparent">
            whole story.
          </span>
        </h1>

        {/* Supporting Narrative */}
        <p className="max-w-3xl mx-auto text-base sm:text-lg text-slate-300 mb-8 leading-relaxed font-normal">
          Traditional keyword detectors flag isolated words out of context — misclassifying friendly peer banter as cyberbullying, while completely missing subtle harassment expressed through sarcasm, unreciprocated ostracism, or repeated targeting asymmetry.
        </p>

        {/* Primary & Secondary Action CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-14">
          <button
            onClick={onStartAnalysis}
            className="flex items-center space-x-2 px-6 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 shadow-lg shadow-teal-500/25 hover:shadow-teal-500/40 transform hover:-translate-y-0.5 transition-all text-sm sm:text-base cursor-pointer"
          >
            <span>Analyze a Conversation</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => onLoadSample('friendly-banter')}
            className="flex items-center space-x-2 px-6 py-3.5 rounded-xl font-semibold text-slate-200 bg-slate-800/90 hover:bg-slate-700/80 border border-slate-700 hover:border-slate-600 transition-all text-sm sm:text-base cursor-pointer"
          >
            <Eye className="w-4 h-4 text-teal-400" />
            <span>Explore Friendly Banter Demo</span>
          </button>

          <button
            onClick={() => onLoadSample('repeated-exclusion')}
            className="flex items-center space-x-2 px-6 py-3.5 rounded-xl font-semibold text-slate-200 bg-slate-800/90 hover:bg-slate-700/80 border border-slate-700 hover:border-slate-600 transition-all text-sm sm:text-base cursor-pointer"
          >
            <Users className="w-4 h-4 text-orange-400" />
            <span>Explore Exclusion Demo</span>
          </button>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-left">
          <div className="glass-card p-5 rounded-xl border border-slate-800/90 hover:border-teal-500/40 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 mb-3">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-100 mb-1">Context Awareness</h3>
            <p className="text-xs text-slate-400 leading-normal">
              Evaluates multi-turn dialogue flow, laughter anchors, and relationship priors rather than single detached keywords.
            </p>
          </div>

          <div className="glass-card p-5 rounded-xl border border-slate-800/90 hover:border-teal-500/40 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-3">
              <MessageSquareDashed className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-100 mb-1">Sarcasm & Banter</h3>
            <p className="text-xs text-slate-400 leading-normal">
              Distinguishes inverted playful praise from harmful mockery by checking listener distress and reciprocal humor.
            </p>
          </div>

          <div className="glass-card p-5 rounded-xl border border-slate-800/90 hover:border-teal-500/40 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400 mb-3">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-100 mb-1">Repeated Targeting</h3>
            <p className="text-xs text-slate-400 leading-normal">
              Identifies power asymmetry and systematic social exclusion where one participant is repeatedly targeted.
            </p>
          </div>

          <div className="glass-card p-5 rounded-xl border border-slate-800/90 hover:border-teal-500/40 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-3">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-100 mb-1">Transparent Evidence</h3>
            <p className="text-xs text-slate-400 leading-normal">
              Provides plain-English reasoning, alternative interpretations, and calibrated confidence for every single turn.
            </p>
          </div>
        </div>

        {/* Privacy Pledge Statement */}
        <div className="mt-8 pt-6 border-t border-slate-800/60 max-w-2xl mx-auto flex items-center justify-center space-x-2 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-teal-400 flex-shrink-0" />
          <span>
            <strong className="text-slate-300">Privacy First:</strong> Conversations are analyzed purely in-memory. No messages are stored in persistent databases or sent to third-party ad networks.
          </span>
        </div>
      </div>
    </section>
  );
};
