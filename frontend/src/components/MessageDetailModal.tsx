import React from 'react';
import { 
  X, 
  HelpCircle, 
  Layers, 
  Compass, 
  Target, 
  CheckCircle, 
  AlertTriangle, 
  ShieldAlert, 
  Flame, 
  Smile, 
  Scale 
} from 'lucide-react';
import type { MessageAnalysis } from '../types';

interface MessageDetailModalProps {
  message: MessageAnalysis | null;
  onClose: () => void;
}

export const MessageDetailModal: React.FC<MessageDetailModalProps> = ({ message, onClose }) => {
  if (!message) return null;

  const getClassificationMeta = (cls: string) => {
    switch (cls) {
      case 'Threat / Urgent Concern':
        return {
          color: 'text-red-400 border-red-500/40 bg-red-500/10',
          badgeText: '[SEVERE THREAT]',
          icon: <Flame className="w-5 h-5 text-red-400" />
        };
      case 'Possible Cyberbullying':
        return {
          color: 'text-orange-400 border-orange-500/40 bg-orange-500/10',
          badgeText: '[CYBERBULLYING]',
          icon: <ShieldAlert className="w-5 h-5 text-orange-400" />
        };
      case 'Potentially Harmful':
        return {
          color: 'text-amber-400 border-amber-500/40 bg-amber-500/10',
          badgeText: '[POTENTIAL HARM]',
          icon: <AlertTriangle className="w-5 h-5 text-amber-400" />
        };
      case 'Friendly Banter':
        return {
          color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10',
          badgeText: '[FRIENDLY BANTER]',
          icon: <Smile className="w-5 h-5 text-emerald-400" />
        };
      case 'Uncertain — More Context Needed':
        return {
          color: 'text-slate-300 border-slate-600 bg-slate-800/60',
          badgeText: '[UNCERTAIN / AMBIGUOUS]',
          icon: <HelpCircle className="w-5 h-5 text-slate-400" />
        };
      case 'Harmless / Neutral':
      default:
        return {
          color: 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10',
          badgeText: '[NEUTRAL]',
          icon: <CheckCircle className="w-5 h-5 text-emerald-400" />
        };
    }
  };

  const meta = getClassificationMeta(message.classification);

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-headline"
    >
      <div 
        className="w-full max-w-2xl bg-navy-900 border border-slate-700 rounded-2xl shadow-2xl p-6 sm:p-7 overflow-y-auto max-h-[90vh] relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header & Close Button */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800 mb-6">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-xl border ${meta.color}`}>
              {meta.icon}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border ${meta.color}`}>
                  {meta.badgeText} {message.classification}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  Turn #{message.id}
                </span>
              </div>
              <h2 id="modal-headline" className="text-lg font-bold text-white mt-1">
                Contextual Explainability Breakdown
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Close message explanation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Highlighted Message Quote */}
        <div className="mb-6 p-4 rounded-xl bg-slate-950/90 border border-slate-800 font-mono text-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5 font-sans">
            <span className="font-semibold text-teal-400">{message.speaker}</span>
            {message.target && (
              <span className="text-slate-500">directed toward <span className="text-slate-300 font-medium">{message.target}</span></span>
            )}
          </div>
          <p className="text-slate-100 text-base leading-relaxed bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
            "{message.text}"
          </p>
        </div>

        {/* Explainability Fields */}
        <div className="space-y-4 mb-6">
          {/* Detected Pattern */}
          <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-teal-400 mb-1">
              <Layers className="w-4 h-4" />
              <span>Detected Behavioral Pattern</span>
            </div>
            <p className="text-sm font-medium text-slate-200">
              {message.detected_pattern}
            </p>
          </div>

          {/* Contextual Evidence */}
          <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-cyan-400 mb-1.5">
              <Compass className="w-4 h-4" />
              <span>Surrounding Contextual Evidence</span>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {message.contextual_evidence.map((ev, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-teal-400 font-bold">•</span>
                  <span>{ev}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Targeting Pattern */}
          <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-orange-400 mb-1">
              <Target className="w-4 h-4" />
              <span>Participant Targeting Dynamic</span>
            </div>
            <p className="text-xs text-slate-300">
              {message.targeting_pattern}
            </p>
          </div>

          {/* Alternative Interpretation */}
          {message.alternative_interpretation && (
            <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800">
              <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-violet-400 mb-1">
                <Scale className="w-4 h-4" />
                <span>Possible Alternative Interpretation</span>
              </div>
              <p className="text-xs text-slate-300 italic">
                "{message.alternative_interpretation}"
              </p>
            </div>
          )}

          {/* Calibrated Confidence & Suggested Action */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800">
              <span className="block text-xs font-semibold uppercase text-slate-400 mb-1">Calibrated Confidence</span>
              <div className="flex items-baseline space-x-2">
                <span className="text-lg font-bold font-mono text-white">
                  {(message.confidence_score * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-slate-400">
                  ({message.confidence_category})
                </span>
              </div>
              <span className="text-[10px] text-slate-500 block mt-1">Calibrated on multi-turn evidence</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800">
              <span className="block text-xs font-semibold uppercase text-teal-400 mb-1">Proportionate Action</span>
              <p className="text-xs text-slate-300">
                {message.suggested_action}
              </p>
            </div>
          </div>
        </div>

        {/* Footer Disclaimer */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
          <span>Assists human discernment • Does not infer unstated psychological intent</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Close Explanation
          </button>
        </div>
      </div>
    </div>
  );
};
