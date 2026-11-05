import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  ShieldAlert, 
  Flame, 
  HelpCircle, 
  Smile, 
  CheckCircle2, 
  Info,
  Clock
} from 'lucide-react';
import type { AnalyzeResponse } from '../types';

interface RiskSummaryCardProps {
  results: AnalyzeResponse;
}

export const RiskSummaryCard: React.FC<RiskSummaryCardProps> = ({ results }) => {
  const { overall_risk, risk_score, conversation_summary, metrics, recommendations, confidence } = results;

  // Accessible risk styling
  const getRiskTheme = () => {
    switch (overall_risk) {
      case 'Critical':
        return {
          bg: 'bg-red-500/10 border-red-500/30 text-red-800',
          badge: 'bg-red-500/20 text-red-900 border-red-500/40',
          icon: <Flame className="w-6 h-6 text-red-700 animate-pulse" />,
          label: 'CRITICAL CONCERN',
          subtext: 'Direct violent threat or severe intimidation phrasing detected.'
        };
      case 'High':
        return {
          bg: 'bg-orange-500/10 border-orange-500/30 text-orange-800',
          badge: 'bg-orange-500/20 text-orange-900 border-orange-500/40',
          icon: <ShieldAlert className="w-6 h-6 text-orange-700" />,
          label: 'HIGH RISK / CYBERBULLYING',
          subtext: 'Repeated targeting, unreciprocated ostracism, or systematic hostility.'
        };
      case 'Moderate':
        return {
          bg: 'bg-amber-500/10 border-amber-500/30 text-amber-800',
          badge: 'bg-amber-500/20 text-amber-900 border-amber-500/40',
          icon: <AlertTriangle className="w-6 h-6 text-amber-700" />,
          label: 'MODERATE CONCERN',
          subtext: 'Potentially harmful remarks or sarcastic ambiguity with recipient distress.'
        };
      case 'Low':
      default:
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-800',
          badge: 'bg-emerald-500/20 text-emerald-900 border-emerald-500/40',
          icon: <ShieldCheck className="w-6 h-6 text-emerald-700" />,
          label: 'LOW RISK / LIMITED CONCERN',
          subtext: 'Reciprocal banter, mutual humor, or standard neutral communication.'
        };
    }
  };

  const theme = getRiskTheme();

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-stone-200 shadow-sm mb-8">
      {/* Top Banner: Risk Level & Estimated Score */}
      <div className={`p-5 rounded-xl border ${theme.bg} mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4`}>
        <div className="flex items-start space-x-4">
          <div className="p-3 rounded-xl bg-stone-50/80 border border-stone-200">
            {theme.icon}
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border ${theme.badge}`}>
                {theme.label}
              </span>
              <span className="text-xs font-mono text-stone-600">
                Confidence: <strong className="text-stone-800">{confidence}</strong>
              </span>
            </div>
            <p className="text-sm font-medium mt-1 text-stone-800">
              {theme.subtext}
            </p>
          </div>
        </div>

        {/* Estimated Risk Meter */}
        <div className="w-full md:w-auto flex md:flex-col items-center justify-between md:items-end border-t md:border-t-0 border-stone-200/80 pt-3 md:pt-0">
          <div className="text-left md:text-right">
            <span className="text-xs text-stone-600 block">Estimated Risk Index</span>
            <span className="text-2xl sm:text-3xl font-extrabold font-mono text-stone-900 tracking-tight">
              {risk_score}<span className="text-xs text-stone-600 font-sans"> / 100</span>
            </span>
          </div>
          <span className="text-[10px] text-stone-500 italic block mt-0.5">
            Heuristic index, not a probability
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-stone-100/70 border border-stone-200/80">
          <div className="flex items-center justify-between text-stone-600 mb-1">
            <span className="text-xs">Analyzed Turns</span>
            <Clock className="w-4 h-4 text-stone-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-stone-900">
            {metrics.total_messages}
          </div>
          <div className="text-[11px] text-stone-500 mt-0.5">
            Across {metrics.participant_count} participant{metrics.participant_count === 1 ? '' : 's'}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-stone-100/70 border border-stone-200/80">
          <div className="flex items-center justify-between text-stone-600 mb-1">
            <span className="text-xs">Harmful / Bullying</span>
            <AlertTriangle className="w-4 h-4 text-orange-700" />
          </div>
          <div className="text-2xl font-bold font-mono text-orange-700">
            {metrics.potentially_harmful_count}
          </div>
          <div className="text-[11px] text-stone-500 mt-0.5">
            {metrics.threat_count > 0 ? `${metrics.threat_count} severe threat(s)` : 'Flagged for concern'}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-stone-100/70 border border-stone-200/80">
          <div className="flex items-center justify-between text-stone-600 mb-1">
            <span className="text-xs">Friendly Banter</span>
            <Smile className="w-4 h-4 text-emerald-700" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-700">
            {metrics.friendly_banter_count}
          </div>
          <div className="text-[11px] text-stone-500 mt-0.5">
            Reciprocal playfulness
          </div>
        </div>

        <div className="p-4 rounded-xl bg-stone-100/70 border border-stone-200/80">
          <div className="flex items-center justify-between text-stone-600 mb-1">
            <span className="text-xs">Ambiguous Context</span>
            <HelpCircle className="w-4 h-4 text-stone-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-stone-700">
            {metrics.uncertain_count}
          </div>
          <div className="text-[11px] text-stone-500 mt-0.5">
            Need wider history
          </div>
        </div>
      </div>

      {/* Narrative Summary */}
      <div className="mb-6 p-4 rounded-xl bg-stone-100/50 border border-stone-200/90">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-700 mb-2 flex items-center space-x-1.5">
          <Info className="w-3.5 h-3.5" />
          <span>Contextual Synthesis</span>
        </h3>
        <p className="text-sm text-stone-800 leading-relaxed">
          {conversation_summary}
        </p>
      </div>

      {/* Actionable Next Steps */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-600 mb-3 flex items-center space-x-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
          <span>Recommended Next Steps & Proportionate Safeguards</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {recommendations.map((rec, index) => (
            <div key={index} className="flex items-start space-x-2.5 p-3 rounded-lg bg-stone-100/60 border border-stone-200 text-xs text-stone-700">
              <span className="flex-shrink-0 w-4 h-4 rounded-full bg-teal-500/20 text-emerald-700 flex items-center justify-center font-bold text-[10px] mt-0.5">
                {index + 1}
              </span>
              <span>{rec}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

