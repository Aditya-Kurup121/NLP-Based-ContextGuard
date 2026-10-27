import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Play, 
  AlertCircle, 
  RefreshCw, 
  ShieldCheck, 
  Table
} from 'lucide-react';
import type { BenchmarkEvaluationResult } from '../types';
import { fetchEvaluationBenchmark } from '../services/api';

export const BenchmarkSection: React.FC = () => {
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkEvaluationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvaluationBenchmark();
      setBenchmarkData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to execute benchmark evaluation');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Run evaluation automatically on first mount
    runEvaluation();
  }, []);

  const classes = ['Low', 'Moderate', 'High', 'Critical'];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white">
              Automated Benchmark Evaluation & Metrics
            </h2>
            <p className="text-xs sm:text-sm text-slate-400">
              Evaluates the active NLP engine against a curated, multi-turn dialogue benchmark dataset.
            </p>
          </div>
        </div>

        <button
          onClick={runEvaluation}
          disabled={loading}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-400 hover:to-teal-500 shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Running Evaluation...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Re-Run Benchmark</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {benchmarkData && (
        <>
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-panel p-5 rounded-2xl border border-slate-800">
              <span className="text-xs text-slate-400 block uppercase font-mono mb-1">Total Test Samples</span>
              <span className="text-3xl font-extrabold font-mono text-white">
                {benchmarkData.total_test_samples}
              </span>
              <span className="text-xs text-slate-500 block mt-1">Multi-turn dialogues</span>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-slate-800">
              <span className="text-xs text-slate-400 block uppercase font-mono mb-1">Overall Accuracy</span>
              <span className="text-3xl font-extrabold font-mono text-teal-400">
                {(benchmarkData.overall_accuracy * 100).toFixed(1)}%
              </span>
              <span className="text-xs text-slate-500 block mt-1">Risk category agreement</span>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-slate-800">
              <span className="text-xs text-slate-400 block uppercase font-mono mb-1">Macro F1 Score</span>
              <span className="text-3xl font-extrabold font-mono text-cyan-400">
                {benchmarkData.macro_f1_score.toFixed(3)}
              </span>
              <span className="text-xs text-slate-500 block mt-1">Harmonized precision & recall</span>
            </div>
          </div>

          {/* Confusion Matrix & Per-Class Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Confusion Matrix */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800">
              <h3 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
                <Table className="w-4 h-4 text-cyan-400" />
                <span>Confusion Matrix (Ground Truth vs Predicted)</span>
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Rows represent true risk classes; columns represent engine predictions.
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-center border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2 px-3 text-left">True \ Pred</th>
                      {classes.map(c => (
                        <th key={c} className="py-2 px-2 text-cyan-300">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {classes.map(trueClass => (
                      <tr key={trueClass} className="border-b border-slate-800/60">
                        <td className="py-2.5 px-3 text-left font-bold text-slate-300">
                          {trueClass}
                        </td>
                        {classes.map(predClass => {
                          const val = benchmarkData.confusion_matrix[trueClass]?.[predClass] || 0;
                          const isDiagonal = trueClass === predClass;
                          return (
                            <td 
                              key={predClass} 
                              className={`py-2 px-2 font-bold ${
                                isDiagonal && val > 0 
                                  ? 'bg-teal-500/20 text-teal-300 rounded' 
                                  : val > 0 
                                    ? 'bg-amber-500/20 text-amber-300 rounded' 
                                    : 'text-slate-600'
                              }`}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Per-Class Precision, Recall, F1 */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800">
              <h3 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-teal-400" />
                <span>Per-Class Performance Metrics</span>
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Evaluates detection sensitivity across banter, harassment, and severe threats.
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2 px-2">Class</th>
                      <th className="py-2 px-2 text-center">TP</th>
                      <th className="py-2 px-2 text-center">FP</th>
                      <th className="py-2 px-2 text-right">Precision</th>
                      <th className="py-2 px-2 text-right">Recall</th>
                      <th className="py-2 px-2 text-right text-teal-300">F1 Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {classes.map(c => {
                      const m = benchmarkData.per_class_metrics[c] || {
                        true_positives: 0,
                        false_positives: 0,
                        precision: 0,
                        recall: 0,
                        f1_score: 0
                      };
                      return (
                        <tr key={c} className="border-b border-slate-800/60 text-slate-300">
                          <td className="py-2.5 px-2 font-bold text-white">{c}</td>
                          <td className="py-2.5 px-2 text-center">{m.true_positives}</td>
                          <td className="py-2.5 px-2 text-center text-slate-400">{m.false_positives}</td>
                          <td className="py-2.5 px-2 text-right">{(m.precision * 100).toFixed(0)}%</td>
                          <td className="py-2.5 px-2 text-right">{(m.recall * 100).toFixed(0)}%</td>
                          <td className="py-2.5 px-2 text-right font-bold text-teal-300">{m.f1_score.toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Detailed Test Cases Table */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <h3 className="text-sm font-bold text-white mb-3">
              Individual Benchmark Cases Breakdown
            </h3>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {benchmarkData.detailed_results.map(item => (
                <div 
                  key={item.id} 
                  className={`p-3 rounded-xl border flex items-center justify-between text-xs font-mono ${
                    item.is_correct 
                      ? 'bg-slate-900/40 border-slate-800 text-slate-300' 
                      : 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-slate-400">{item.id}</span>
                    <span>True: <strong className="text-slate-100">{item.true_risk}</strong></span>
                    <span>➔</span>
                    <span>Predicted: <strong className={item.is_correct ? 'text-teal-400' : 'text-amber-400'}>{item.predicted_risk}</strong></span>
                    <span className="text-slate-500">({item.risk_score} / 100)</span>
                  </div>

                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-sans font-bold uppercase ${
                    item.is_correct 
                      ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30' 
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}>
                    {item.is_correct ? 'Match' : 'Calibrated Ambiguity'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Dataset Acquisition & Ethical Guidelines Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/30 text-xs text-slate-300 space-y-3">
        <div className="flex items-center space-x-2 text-teal-400 font-bold uppercase tracking-wider">
          <ShieldCheck className="w-4 h-4" />
          <span>Dataset Ethics, Privacy & Licensing Notice</span>
        </div>
        <p className="leading-relaxed">
          <strong>Academic Dataset Sources:</strong> Researchers seeking real-world cyberbullying corpora should consult publicly cataloged datasets such as <em>Davidson et al. (Automated Hate Speech Detection and the Problem of Offensive Language)</em>, <em>Waseem and Hovy (Hateful Symbols or Hateful People)</em>, or the <em>Kaggle Jigsaw Toxic Comment Classification Challenge</em>.
        </p>
        <p className="leading-relaxed text-slate-400">
          <strong>Privacy Safeguards:</strong> Under privacy regulations (GDPR / FERPA / COPPA), private personal chat logs should never be uploaded into public cloud endpoints without explicit participant consent and anonymization.
        </p>
      </div>
    </div>
  );
};
