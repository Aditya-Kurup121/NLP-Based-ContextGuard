import React from 'react';
import { Shield, Sparkles, BookOpen, Activity, Lock, BarChart3 } from 'lucide-react';

interface NavbarProps {
  activeTab: 'analyzer' | 'network' | 'methodology' | 'benchmark';
  setActiveTab: (tab: 'analyzer' | 'network' | 'methodology' | 'benchmark') => void;
  backendOnline: boolean;
  onClearAll: () => void;
  hasResults: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  backendOnline,
  onClearAll,
  hasResults,
}) => {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-navy-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('analyzer')}>
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-indigo-600 shadow-lg shadow-teal-500/20">
              <Shield className="w-5 h-5 text-white" />
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${backendOnline ? 'bg-teal-400' : 'bg-amber-400'} opacity-75`}></span>
                <span className={`relative inline-flex rounded-full h-3 w-3 ${backendOnline ? 'bg-teal-500' : 'bg-amber-500'}`}></span>
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-teal-400 via-cyan-200 to-indigo-300 bg-clip-text text-transparent">
                  ContextGuard
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-mono font-medium bg-teal-500/10 text-teal-300 border border-teal-500/20">
                  v1.2 NLP
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Understand the context. Detect the harm.
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('analyzer')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'analyzer'
                  ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Analyzer</span>
            </button>

            <button
              onClick={() => setActiveTab('network')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'network'
                  ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span className="hidden sm:inline">Interaction</span> Matrix
            </button>

            <button
              onClick={() => setActiveTab('methodology')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'methodology'
                  ? 'bg-violet-500/15 text-violet-300 border border-violet-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>Methodology</span>
            </button>

            <button
              onClick={() => setActiveTab('benchmark')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'benchmark'
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span className="hidden sm:inline">Benchmark</span> Evaluation
            </button>
          </nav>

          {/* Right Status Pill & Clear Data */}
          <div className="hidden md:flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-slate-900 border border-slate-800 text-slate-300">
              <Lock className="w-3 h-3 text-teal-400" />
              <span>Zero Cloud Leak</span>
            </div>

            {hasResults && (
              <button
                onClick={onClearAll}
                className="text-xs px-2.5 py-1 rounded-lg text-slate-400 hover:text-red-300 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-colors"
                title="Wipe analysis results from browser memory"
              >
                Clear Data
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
