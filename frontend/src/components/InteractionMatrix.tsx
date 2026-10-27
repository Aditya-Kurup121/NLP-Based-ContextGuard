import React from 'react';
import { Users, ArrowRight, ShieldAlert, AlertCircle, BarChart2 } from 'lucide-react';
import type { ParticipantInfo, TargetingInteraction, MessageAnalysis } from '../types';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

interface InteractionMatrixProps {
  participants: ParticipantInfo[];
  targetingPatterns: TargetingInteraction[];
  messages: MessageAnalysis[];
}

export const InteractionMatrix: React.FC<InteractionMatrixProps> = ({
  participants,
  targetingPatterns,
  messages,
}) => {
  // Chart data preparing
  const chartData = participants.map((p) => ({
    name: p.name,
    totalSent: p.messages_sent,
    harmfulSent: p.harmful_sent,
    targeted: p.targeted_count,
  }));

  // Identify most concerning messages
  const concerningMessages = messages.filter(m =>
    ['Threat / Urgent Concern', 'Possible Cyberbullying', 'Potentially Harmful'].includes(m.classification)
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Overview Header */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white">
              Participant Interaction & Targeting Dynamics
            </h2>
            <p className="text-xs sm:text-sm text-slate-400">
              Analyzes who directs hostility or playful banter toward whom. Assesses targeting asymmetry rather than isolated words.
            </p>
          </div>
        </div>

        {/* Responsible AI Disclaimer */}
        <div className="mt-4 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
          <span>
            <strong>Ethical AI Guardrail:</strong> ContextGuard evaluates conversation structures and repeated asymmetry. It does NOT generate definitive psychological profiles or label individuals as permanent bullies.
          </span>
        </div>
      </div>

      {/* Participants Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {participants.map((p) => {
          const isTargetedVictim = p.targeted_count >= 2 && p.harmful_sent === 0;
          const isFrequentHostile = p.harmful_sent >= 2;

          return (
            <div 
              key={p.name}
              className={`glass-panel p-5 rounded-2xl border transition-all ${
                isFrequentHostile 
                  ? 'border-orange-500/30 bg-orange-950/10' 
                  : isTargetedVictim 
                    ? 'border-red-500/30 bg-red-950/10'
                    : 'border-slate-800 bg-slate-900/40'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2.5">
                  <div className="w-9 h-9 rounded-xl bg-slate-800 text-teal-300 font-bold flex items-center justify-center border border-slate-700">
                    {p.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">{p.name}</h3>
                    <span className="text-[11px] text-slate-400">Participant</span>
                  </div>
                </div>

                {isFrequentHostile && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-300 border border-orange-500/30">
                    Hostility Source
                  </span>
                )}
                {isTargetedVictim && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
                    Repeated Target
                  </span>
                )}
              </div>

              {/* Stats Counters */}
              <div className="grid grid-cols-3 gap-2 py-3 border-y border-slate-800/80 mb-3 text-center">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Sent</span>
                  <span className="text-base font-bold font-mono text-white">{p.messages_sent}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Harmful</span>
                  <span className={`text-base font-bold font-mono ${p.harmful_sent > 0 ? 'text-orange-400' : 'text-slate-400'}`}>
                    {p.harmful_sent}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Targeted</span>
                  <span className={`text-base font-bold font-mono ${p.targeted_count > 0 ? 'text-red-400' : 'text-slate-400'}`}>
                    {p.targeted_count}
                  </span>
                </div>
              </div>

              {/* Role Summary */}
              <p className="text-xs text-slate-300 leading-normal">
                {p.role_summary}
              </p>
            </div>
          );
        })}
      </div>

      {/* Targeting Patterns & Asymmetry Table */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <h3 className="text-base font-bold text-white mb-3 flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-orange-400" />
          <span>Directed Hostility & Banter Matrix</span>
        </h3>

        {targetingPatterns.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800">
            No repeated directed hostility or targeting detected in this conversation.
          </div>
        ) : (
          <div className="space-y-3">
            {targetingPatterns.map((tp, idx) => (
              <div 
                key={idx}
                className={`p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
                  tp.is_asymmetric 
                    ? 'bg-orange-950/20 border-orange-500/40' 
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1.5 font-mono text-sm font-bold text-white">
                    <span className="text-orange-400">{tp.source}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-teal-400">{tp.target}</span>
                  </div>

                  {tp.is_asymmetric && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30 uppercase">
                      Asymmetric Target
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-4 text-xs">
                  <span className="text-slate-400">
                    Hostile turns: <strong className="text-orange-400 font-mono">{tp.harmful_turns}</strong>
                  </span>
                  <span className="text-slate-400">
                    Banter turns: <strong className="text-teal-400 font-mono">{tp.banter_turns}</strong>
                  </span>
                </div>

                <p className="text-xs text-slate-300 w-full sm:w-auto">
                  {tp.description}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Visual Analytics Chart */}
      {chartData.length > 0 && (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
            <BarChart2 className="w-4 h-4 text-teal-400" />
            <span>Turn Distribution by Participant</span>
          </h3>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="totalSent" name="Total Turns Sent" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="harmfulSent" name="Harmful Turns Sent" fill="#f97316" radius={[4, 4, 0, 0]} />
                <Bar dataKey="targeted" name="Targeted Count" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Most Concerning Messages Callout */}
      {concerningMessages.length > 0 && (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <h3 className="text-base font-bold text-white mb-3 text-orange-400 flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4" />
            <span>Key Concerning Turns ({concerningMessages.length})</span>
          </h3>
          <div className="space-y-2.5">
            {concerningMessages.map((cm) => (
              <div key={cm.id} className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-3 text-xs">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-bold text-slate-200">{cm.speaker}</span>
                    <span className="text-slate-500 font-mono">Turn #{cm.id}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-orange-300 font-medium">
                      {cm.detected_pattern}
                    </span>
                  </div>
                  <p className="text-slate-100 font-mono bg-slate-950 px-2 py-1 rounded border border-slate-800">
                    "{cm.text}"
                  </p>
                </div>
                <span className="text-[11px] font-bold text-orange-400 whitespace-nowrap self-center">
                  {cm.classification}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
