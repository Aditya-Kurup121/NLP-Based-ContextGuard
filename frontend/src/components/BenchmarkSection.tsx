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
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-stone-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-emerald-700">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-stone-900">
              Regression Examples
            </h2>
            <p className="text-xs sm:text-sm text-stone-600">
              A sanity check on 10 hand-written synthetic conversations that the rules were developed against. It is not an evaluation: scores here say nothing about performance on unseen conversations. See Language lab → Model evidence for the held-out evaluation.
            </p>
          </div>
        </div>

        <button
          onClick={runEvaluation}
          disabled={loading}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-emerald-800     shadow-sm shadow-cyan-500/20 transition-all disabled:opacity-50 cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Running Evaluation...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Re-Run Examples</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {benchmarkData && (
        <>
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-panel p-5 rounded-2xl border border-stone-200">
              <span className="text-xs text-stone-600 block uppercase font-mono mb-1">Regression Examples</span>
              <span className="text-3xl font-extrabold font-mono text-stone-900">
                {benchmarkData.total_test_samples}
              </span>
              <span className="text-xs text-stone-500 block mt-1">Multi-turn dialogues</span>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-stone-200">
              <span className="text-xs text-stone-600 block uppercase font-mono mb-1">Examples Passing</span>
              <span className="text-3xl font-extrabold font-mono text-emerald-700">
                {(benchmarkData.overall_accuracy * 100).toFixed(1)}%
              </span>
              <span className="text-xs text-stone-500 block mt-1">Risk category agreement</span>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-stone-200">
              <span className="text-xs text-stone-600 block uppercase font-mono mb-1">Macro F1 Score</span>
              <span className="text-3xl font-extrabold font-mono text-emerald-700">
                {benchmarkData.macro_f1_score.toFixed(3)}
              </span>
              <span className="text-xs text-stone-500 block mt-1">Harmonized precision & recall</span>
            </div>
          </div>

          {/* Confusion Matrix & Per-Class Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Confusion Matrix */}
            <div className="glass-panel p-6 rounded-2xl border border-stone-200">
              <h3 className="text-sm font-bold text-stone-900 mb-3 flex items-center space-x-2">
                <Table className="w-4 h-4 text-emerald-700" />
                <span>Confusion Matrix (Ground Truth vs Predicted)</span>
              </h3>
              <p className="text-xs text-stone-600 mb-4">
                Rows represent true risk classes; columns represent engine predictions.
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-center border-collapse">
                  <thead>
                    <tr className="border-b border-stone-200 text-stone-600">
                      <th className="py-2 px-3 text-left">True \ Pred</th>
                      {classes.map(c => (
                        <th key={c} className="py-2 px-2 text-emerald-800">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {classes.map(trueClass => (
                      <tr key={trueClass} className="border-b border-stone-200/60">
                        <td className="py-2.5 px-3 text-left font-bold text-stone-700">
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
                                  ? 'bg-teal-500/20 text-emerald-800 rounded' 
                                  : val > 0 
                                    ? 'bg-amber-500/20 text-amber-800 rounded' 
                                    : 'text-stone-500'
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
            <div className="glass-panel p-6 rounded-2xl border border-stone-200">
              <h3 className="text-sm font-bold text-stone-900 mb-3 flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-emerald-700" />
                <span>Per-Class Performance Metrics</span>
              </h3>
              <p className="text-xs text-stone-600 mb-4">
                Evaluates detection sensitivity across banter, harassment, and severe threats.
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-left border-collapse">
                  <thead>
                    <tr className="border-b border-stone-200 text-stone-600">
                      <th className="py-2 px-2">Class</th>
                      <th className="py-2 px-2 text-center">TP</th>
                      <th className="py-2 px-2 text-center">FP</th>
                      <th className="py-2 px-2 text-right">Precision</th>
                      <th className="py-2 px-2 text-right">Recall</th>
                      <th className="py-2 px-2 text-right text-emerald-800">F1 Score</th>
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
                        <tr key={c} className="border-b border-stone-200/60 text-stone-700">
                          <td className="py-2.5 px-2 font-bold text-stone-900">{c}</td>
                          <td className="py-2.5 px-2 text-center">{m.true_positives}</td>
                          <td className="py-2.5 px-2 text-center text-stone-600">{m.false_positives}</td>
                          <td className="py-2.5 px-2 text-right">{(m.precision * 100).toFixed(0)}%</td>
                          <td className="py-2.5 px-2 text-right">{(m.recall * 100).toFixed(0)}%</td>
                          <td className="py-2.5 px-2 text-right font-bold text-emerald-800">{m.f1_score.toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Detailed Test Cases Table */}
          <div className="glass-panel p-6 rounded-2xl border border-stone-200">
            <h3 className="text-sm font-bold text-stone-900 mb-3">
              Individual Benchmark Cases Breakdown
            </h3>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {benchmarkData.detailed_results.map(item => (
                <div 
                  key={item.id} 
                  className={`p-3 rounded-xl border flex items-center justify-between text-xs font-mono ${
                    item.is_correct 
                      ? 'bg-stone-100/40 border-stone-200 text-stone-700' 
                      : 'bg-amber-100/20 border-amber-500/30 text-amber-900'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-stone-600">{item.id}</span>
                    <span>True: <strong className="text-stone-800">{item.true_risk}</strong></span>
                    <span>➔</span>
                    <span>Predicted: <strong className={item.is_correct ? 'text-emerald-700' : 'text-amber-700'}>{item.predicted_risk}</strong></span>
                    <span className="text-stone-500">({item.risk_score} / 100)</span>
                  </div>

                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-sans font-bold uppercase ${
                    item.is_correct 
                      ? 'bg-teal-500/20 text-emerald-800 border border-teal-500/30' 
                      : 'bg-amber-500/20 text-amber-800 border border-amber-500/30'
                  }`}>
                    {item.is_correct ? 'Match' : 'Mismatch'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Dataset Acquisition & Ethical Guidelines Card */}
      <div className="glass-panel p-6 rounded-2xl border border-stone-200 bg-stone-100/30 text-xs text-stone-700 space-y-3">
        <div className="flex items-center space-x-2 text-emerald-700 font-bold uppercase tracking-wider">
          <ShieldCheck className="w-4 h-4" />
          <span>Dataset Ethics, Privacy & Licensing Notice</span>
        </div>
        <p className="leading-relaxed">
          <strong>Academic Dataset Sources:</strong> Researchers seeking real-world cyberbullying corpora should consult publicly cataloged datasets such as <em>Davidson et al. (Automated Hate Speech Detection and the Problem of Offensive Language)</em>, <em>Waseem and Hovy (Hateful Symbols or Hateful People)</em>, or the <em>Kaggle Jigsaw Toxic Comment Classification Challenge</em>.
        </p>
        <p className="leading-relaxed text-stone-600">
          <strong>Privacy Safeguards:</strong> Under privacy regulations (GDPR / FERPA / COPPA), private personal chat logs should never be uploaded into public cloud endpoints without explicit participant consent and anonymization.
        </p>
      </div>
    </div>
  );
};

