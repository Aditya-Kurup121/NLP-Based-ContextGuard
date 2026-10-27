import React, { useState } from 'react';
import { 
  Smile, 
  AlertTriangle, 
  ShieldAlert, 
  Flame, 
  HelpCircle, 
  CheckCircle, 
  MessageSquare, 
  Filter,
  ChevronRight
} from 'lucide-react';
import type { MessageAnalysis } from '../types';

interface ConversationTimelineProps {
  messages: MessageAnalysis[];
  onSelectMessage: (message: MessageAnalysis) => void;
}

export const ConversationTimeline: React.FC<ConversationTimelineProps> = ({ messages, onSelectMessage }) => {
  const [filter, setFilter] = useState<string>('all');

  const filteredMessages = messages.filter(m => {
    if (filter === 'harmful') {
      return ['Potentially Harmful', 'Possible Cyberbullying', 'Threat / Urgent Concern'].includes(m.classification);
    }
    if (filter === 'banter') {
      return m.classification === 'Friendly Banter';
    }
    if (filter === 'uncertain') {
      return m.classification === 'Uncertain — More Context Needed';
    }
    return true;
  });

  const getStyleTokens = (classification: string) => {
    switch (classification) {
      case 'Threat / Urgent Concern':
        return {
          border: 'border-red-500/50 bg-red-950/20 hover:border-red-400',
          badge: 'bg-red-500/20 text-red-200 border-red-500/40',
          badgePrefix: '🔴 THREAT',
          icon: <Flame className="w-4 h-4 text-red-400" />,
          avatarBg: 'bg-red-900/60 text-red-200 border border-red-700/50'
        };
      case 'Possible Cyberbullying':
        return {
          border: 'border-orange-500/50 bg-orange-950/20 hover:border-orange-400',
          badge: 'bg-orange-500/20 text-orange-200 border-orange-500/40',
          badgePrefix: '🟠 CYBERBULLYING',
          icon: <ShieldAlert className="w-4 h-4 text-orange-400" />,
          avatarBg: 'bg-orange-900/60 text-orange-200 border border-orange-700/50'
        };
      case 'Potentially Harmful':
        return {
          border: 'border-amber-500/50 bg-amber-950/20 hover:border-amber-400',
          badge: 'bg-amber-500/20 text-amber-200 border-amber-500/40',
          badgePrefix: '🟡 POTENTIALLY HARMFUL',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          avatarBg: 'bg-amber-900/60 text-amber-200 border border-amber-700/50'
        };
      case 'Friendly Banter':
        return {
          border: 'border-emerald-500/40 bg-emerald-950/15 hover:border-emerald-400',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          badgePrefix: '🟢 FRIENDLY BANTER',
          icon: <Smile className="w-4 h-4 text-emerald-400" />,
          avatarBg: 'bg-emerald-900/60 text-emerald-200 border border-emerald-700/50'
        };
      case 'Uncertain — More Context Needed':
        return {
          border: 'border-slate-600/50 bg-slate-900/60 hover:border-slate-500',
          badge: 'bg-slate-700/50 text-slate-300 border-slate-600',
          badgePrefix: '⚪ UNCERTAIN CONTEXT',
          icon: <HelpCircle className="w-4 h-4 text-slate-400" />,
          avatarBg: 'bg-slate-800 text-slate-300 border border-slate-700'
        };
      case 'Harmless / Neutral':
      default:
        return {
          border: 'border-slate-800 bg-slate-950/60 hover:border-slate-700',
          badge: 'bg-slate-800 text-slate-300 border-slate-700',
          badgePrefix: '🟢 HARMLESS / NEUTRAL',
          icon: <CheckCircle className="w-4 h-4 text-slate-400" />,
          avatarBg: 'bg-slate-800 text-slate-300 border border-slate-700'
        };
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl mb-8">
      {/* Header and Filter Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <MessageSquare className="w-5 h-5 text-teal-400" />
            <span>Interactive Conversation Timeline</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Click any turn to inspect multi-turn context, pattern evidence, alternative interpretations, and signals.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 self-stretch sm:self-auto overflow-x-auto pb-1 sm:pb-0">
          <Filter className="w-3.5 h-3.5 text-slate-500 mr-1 hidden sm:inline" />
          <button
            onClick={() => setFilter('all')}
            className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800'
            }`}
          >
            All ({messages.length})
          </button>
          <button
            onClick={() => setFilter('harmful')}
            className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-colors ${
              filter === 'harmful'
                ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800'
            }`}
          >
            Concern / Threats
          </button>
          <button
            onClick={() => setFilter('banter')}
            className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-colors ${
              filter === 'banter'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800'
            }`}
          >
            Friendly Banter
          </button>
          <button
            onClick={() => setFilter('uncertain')}
            className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-colors ${
              filter === 'uncertain'
                ? 'bg-slate-700/50 text-slate-200 border border-slate-600'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800'
            }`}
          >
            Ambiguous
          </button>
        </div>
      </div>

      {/* Message Cards List */}
      <div className="space-y-3.5">
        {filteredMessages.map((msg) => {
          const style = getStyleTokens(msg.classification);
          const isFlagged = ['Potentially Harmful', 'Possible Cyberbullying', 'Threat / Urgent Concern'].includes(msg.classification);

          return (
            <div
              key={msg.id}
              onClick={() => onSelectMessage(msg)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectMessage(msg);
                }
              }}
              tabIndex={0}
              role="button"
              aria-label={`Inspect turn #${msg.id} by ${msg.speaker}: ${msg.classification}`}
              className={`group p-4 rounded-xl border ${style.border} transition-all duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-500/50 relative`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start space-x-3 w-full">
                  {/* Speaker Avatar */}
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0 ${style.avatarBg}`}>
                    {msg.speaker.slice(0, 2).toUpperCase()}
                  </div>

                  {/* Message Body */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="text-xs font-bold text-slate-200">
                        {msg.speaker}
                      </span>
                      {msg.target && (
                        <span className="text-[11px] text-slate-500 font-sans">
                          ➔ {msg.target}
                        </span>
                      )}
                      <span className="text-[11px] font-mono text-slate-600">
                        #{msg.id}
                      </span>

                      {/* Accessible Classification Badge */}
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${style.badge} flex items-center space-x-1 ml-auto`}>
                        {style.icon}
                        <span>{style.badgePrefix}</span>
                      </span>
                    </div>

                    {/* Utterance Text */}
                    <p className={`text-sm sm:text-base leading-relaxed ${isFlagged ? 'text-white font-medium' : 'text-slate-300'}`}>
                      {msg.text}
                    </p>

                    {/* Detected Signals Row */}
                    <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] text-slate-500 uppercase font-mono mr-1">Pattern:</span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 font-medium">
                        {msg.detected_pattern}
                      </span>

                      {msg.signals.has_laughter && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          😂 Laughter Cue
                        </span>
                      )}
                      {msg.signals.is_reciprocal_tease && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">
                          🔄 Reciprocal Banter
                        </span>
                      )}
                      {msg.signals.is_sarcasm_suspect && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-300 border border-violet-500/20">
                          🎭 Sarcasm Suspect
                        </span>
                      )}
                      {msg.signals.has_exclusion_phrase && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-300 border border-orange-500/20 font-bold">
                          🚫 Exclusion Phrase
                        </span>
                      )}
                      {msg.signals.is_repeated_target && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-300 border border-red-500/20 font-bold">
                          🎯 Repeated Target
                        </span>
                      )}
                      {msg.signals.is_victim_protest && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          🛑 Participant Protest
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Inspect Chevron */}
                <div className="flex items-center text-slate-500 group-hover:text-teal-400 transition-colors pt-1">
                  <span className="text-xs hidden md:inline mr-1 opacity-0 group-hover:opacity-100 transition-opacity">Explain</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
