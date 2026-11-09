import React from 'react';
import { ScanLine, ArrowUpRight } from 'lucide-react';
type Tab = 'analyzer' | 'network' | 'methodology' | 'benchmark' | 'lab' | 'import';
interface NavbarProps { activeTab: Tab; setActiveTab: (tab: Tab) => void; backendOnline: boolean; onClearAll: () => void; hasResults: boolean }
export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, backendOnline, onClearAll, hasResults }) => (
<header className="workspace-header"><div className="header-inner"><button className="brand" onClick={() => setActiveTab('analyzer')} aria-label="ContextGuard home"><span className="brand-mark"><ScanLine size={24} /></span>ContextGuard<span className="brand-caption">RESEARCH STUDIO</span></button><div className="service-status" role="status"><i className={backendOnline ? 'online' : ''} />{backendOnline ? 'Local engine connected' : 'Local engine offline'}</div></div><div className="navigation-inner"><nav aria-label="Main navigation">{([['analyzer', 'Review workspace'], ['import', 'Import WhatsApp'], ['network', 'Interaction map'], ['lab', 'Language lab'], ['methodology', 'How it works'], ['benchmark', 'Regression examples']] as [Tab, string][]).map(([tab, label], i) => <button key={tab} aria-current={activeTab === tab ? 'page' : undefined} className={activeTab === tab ? 'selected' : ''} onClick={() => setActiveTab(tab)}><span>0{i + 1}</span>{label}</button>)}</nav>{hasResults && <button className="new-review" onClick={onClearAll}>New review <ArrowUpRight size={15} /></button>}</div></header>
);

