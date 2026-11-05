import React, { useEffect, useRef } from 'react';
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
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!message) return;
    const previous = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialogRef.current?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab') {
        const controls = dialogRef.current?.querySelectorAll<HTMLElement>('button, a[href], input, select, textarea, [tabindex="0"]');
        if (!controls?.length) { event.preventDefault(); return; }
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialogRef.current)) { event.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener('keydown', keydown);
    return () => { document.removeEventListener('keydown', keydown); document.body.style.overflow = previousOverflow; previous?.focus(); };
  }, [message, onClose]);
  if (!message) return null;

  const getClassificationMeta = (cls: string) => {
    switch (cls) {
      case 'Threat / Urgent Concern':
        return {
          color: 'text-red-700 border-red-500/40 bg-red-500/10',
          badgeText: '[SEVERE THREAT]',
          icon: <Flame className="w-5 h-5 text-red-700" />
        };
      case 'Possible Cyberbullying':
        return {
          color: 'text-orange-700 border-orange-500/40 bg-orange-500/10',
          badgeText: '[CYBERBULLYING]',
          icon: <ShieldAlert className="w-5 h-5 text-orange-700" />
        };
      case 'Potentially Harmful':
        return {
          color: 'text-amber-700 border-amber-500/40 bg-amber-500/10',
          badgeText: '[POTENTIAL HARM]',
          icon: <AlertTriangle className="w-5 h-5 text-amber-700" />
        };
      case 'Friendly Banter':
        return {
          color: 'text-emerald-700 border-emerald-500/40 bg-emerald-500/10',
          badgeText: '[FRIENDLY BANTER]',
          icon: <Smile className="w-5 h-5 text-emerald-700" />
        };
      case 'Uncertain — More Context Needed':
        return {
          color: 'text-stone-700 border-stone-300 bg-stone-200/60',
          badgeText: '[UNCERTAIN / AMBIGUOUS]',
          icon: <HelpCircle className="w-5 h-5 text-stone-600" />
        };
      case 'Harmless / Neutral':
      default:
        return {
          color: 'text-emerald-800 border-emerald-500/30 bg-emerald-500/10',
          badgeText: '[NEUTRAL]',
          icon: <CheckCircle className="w-5 h-5 text-emerald-700" />
        };
    }
  };

  const meta = getClassificationMeta(message.classification);

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-50/80 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-headline"
      ref={dialogRef}
      tabIndex={-1}
    >
      <div 
        className="w-full max-w-2xl bg-white border border-stone-300 rounded-2xl shadow-sm p-6 sm:p-7 overflow-y-auto max-h-[90vh] relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header & Close Button */}
        <div className="flex items-start justify-between pb-4 border-b border-stone-200 mb-6">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-xl border ${meta.color}`}>
              {meta.icon}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border ${meta.color}`}>
                  {meta.badgeText} {message.classification}
                </span>
                <span className="text-xs font-mono text-stone-600">
                  Turn #{message.id}
                </span>
              </div>
              <h2 id="modal-headline" className="text-lg font-bold text-stone-900 mt-1">
                Contextual Explainability Breakdown
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-600 hover:text-stone-900 hover:bg-stone-200 transition-colors"
            aria-label="Close message explanation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Highlighted Message Quote */}
        <div className="mb-6 p-4 rounded-xl bg-stone-50/90 border border-stone-200 font-mono text-sm">
          <div className="flex items-center justify-between text-xs text-stone-600 mb-1.5 font-sans">
            <span className="font-semibold text-emerald-700">{message.speaker}</span>
            {message.target && (
              <span className="text-stone-500">directed toward <span className="text-stone-700 font-medium">{message.target}</span></span>
            )}
          </div>
          <p className="text-stone-800 text-base leading-relaxed bg-stone-100/60 p-2.5 rounded-lg border border-stone-200/80">
            "{message.text}"
          </p>
        </div>

        {/* Explainability Fields */}
        {message.statistical_assessment && <section className="statistical-evidence">
          <p className="eyebrow">A SECOND LOCAL SIGNAL</p>
          <h3>What the trained classifier sees</h3>
          <p><strong>{message.statistical_assessment.label}</strong> · score {message.statistical_assessment.toxicity_score.toFixed(3)} · {message.statistical_assessment.model}</p>
          <div className="feature-chips">{message.statistical_assessment.top_features.map(feature => <span key={feature.term} title={`Contribution to toxic log-odds: ${feature.contribution}`} className={feature.contribution > 0 ? 'toward-toxic' : 'away-toxic'}>{feature.term} {feature.contribution > 0 ? '+' : '−'}</span>)}</div>
          <p className="lab-note">{message.statistical_assessment.note} Feature contributions describe this model, not the speaker’s intent.</p>
        </section>}
        <div className="space-y-4 mb-6">
          {/* Detected Pattern */}
          <div className="p-3.5 rounded-xl bg-stone-200/40 border border-stone-200">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-emerald-700 mb-1">
              <Layers className="w-4 h-4" />
              <span>Detected Behavioral Pattern</span>
            </div>
            <p className="text-sm font-medium text-stone-800">
              {message.detected_pattern}
            </p>
          </div>

          {/* Contextual Evidence */}
          <div className="p-3.5 rounded-xl bg-stone-200/40 border border-stone-200">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-emerald-700 mb-1.5">
              <Compass className="w-4 h-4" />
              <span>Surrounding Contextual Evidence</span>
            </div>
            <ul className="space-y-1.5 text-xs text-stone-700">
              {message.contextual_evidence.map((ev, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-emerald-700 font-bold">•</span>
                  <span>{ev}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Targeting Pattern */}
          <div className="p-3.5 rounded-xl bg-stone-200/40 border border-stone-200">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-orange-700 mb-1">
              <Target className="w-4 h-4" />
              <span>Participant Targeting Dynamic</span>
            </div>
            <p className="text-xs text-stone-700">
              {message.targeting_pattern}
            </p>
          </div>

          {/* Alternative Interpretation */}
          {message.alternative_interpretation && (
            <div className="p-3.5 rounded-xl bg-stone-200/40 border border-stone-200">
              <div className="flex items-center space-x-2 text-xs font-semibold uppercase text-stone-600 mb-1">
                <Scale className="w-4 h-4" />
                <span>Possible Alternative Interpretation</span>
              </div>
              <p className="text-xs text-stone-700 italic">
                "{message.alternative_interpretation}"
              </p>
            </div>
          )}

          {/* Calibrated Confidence & Suggested Action */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-stone-200/40 border border-stone-200">
              <span className="block text-xs font-semibold uppercase text-stone-600 mb-1">Heuristic confidence</span>
              <div className="flex items-baseline space-x-2">
                <span className="text-lg font-bold font-mono text-stone-900">
                  {(message.confidence_score * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-stone-600">
                  ({message.confidence_category})
                </span>
              </div>
              <span className="text-[10px] text-stone-500 block mt-1">Rule-assigned score; not statistically calibrated</span>
            </div>

            <div className="p-3.5 rounded-xl bg-stone-200/40 border border-stone-200">
              <span className="block text-xs font-semibold uppercase text-emerald-700 mb-1">Proportionate Action</span>
              <p className="text-xs text-stone-700">
                {message.suggested_action}
              </p>
            </div>
          </div>
        </div>

        {/* Footer Disclaimer */}
        <div className="pt-4 border-t border-stone-200 flex items-center justify-between text-xs text-stone-500">
          <span>Assists human discernment • Does not infer unstated psychological intent</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-stone-200 hover:bg-stone-200 text-stone-800 text-xs font-medium transition-colors"
          >
            Close Explanation
          </button>
        </div>
      </div>
    </div>
  );
};
