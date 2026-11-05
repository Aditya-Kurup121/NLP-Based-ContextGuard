import React, { useState } from 'react';
import { ArrowRight, ChevronDown, RotateCcw, AlertCircle } from 'lucide-react';
import type { ExampleConversation, ContextInfo } from '../types';
interface AnalyzerFormProps {
 conversationText: string; setConversationText: (text: string) => void;
 contextInfo: ContextInfo; setContextInfo: React.Dispatch<React.SetStateAction<ContextInfo>>;
 examples: ExampleConversation[]; onSelectExample: (example: ExampleConversation) => void;
 onAnalyze: () => void; isLoading: boolean; onClear: () => void; error: string | null;
}
export const AnalyzerForm: React.FC<AnalyzerFormProps> = ({ conversationText, setConversationText, contextInfo, setContextInfo, examples, onSelectExample, onAnalyze, isLoading, onClear, error }) => {
 const [showContext, setShowContext] = useState(false);
 const [view, setView] = useState<'edit' | 'preview'>('edit');
 const lines = conversationText.split('\n').filter(line => line.trim());
 const names = [...new Set(lines.map(line => line.match(/^([^:]{1,35}):\s*/)?.[1]?.trim()).filter(Boolean))];
 return <section id="analyzer-form-section" className="review-editor" aria-busy={isLoading}>
 <div className="editor-heading"><div><p className="eyebrow">01 / THE CONVERSATION</p><h2>Bring the whole conversation.</h2><p>Include the replies. They often change the picture.</p></div><div className="view-switch" aria-label="Input view"><button onClick={() => setView('edit')} aria-pressed={view === 'edit'}>Write</button><button onClick={() => setView('preview')} aria-pressed={view === 'preview'}>Preview</button></div></div>
 <div className="editor-layout"><div className="editor-main"><label htmlFor="conversation-input" className="input-label">Conversation transcript <span>Speaker: Message</span></label>
 {view === 'edit' ? <textarea id="conversation-input" maxLength={50000} value={conversationText} disabled={isLoading} onChange={e => setConversationText(e.target.value)} placeholder={'Alice: Nice shot, professional athlete 😂\nBob: Says the person who missed an empty goal.\nAlice: Okay bro, rematch tomorrow.'} rows={9} /> : <div className="chat-preview" aria-label="Transcript preview">{lines.length ? lines.map((line, i) => { const match = line.match(/^([^:]{1,35}):\s*(.*)$/); return <div className="preview-message" key={i}><span className="preview-avatar">{(match?.[1] || '?').slice(0, 1).toUpperCase()}</span><div><strong>{match?.[1] || 'Continuation / unlabeled'}</strong><p>{match?.[2] ?? line}</p></div></div>; }) : <p className="empty-preview">Write a conversation to preview it here.</p>}</div>}
 <div className="editor-meta"><span>{lines.length} non-empty lines · {names.length} labeled speakers</span><span>{conversationText.length.toLocaleString()} / 50,000</span></div>
 <button className="context-toggle" onClick={() => setShowContext(!showContext)} aria-expanded={showContext} aria-controls="context-fields">Relationship & setting <span>Optional <ChevronDown size={14} /></span></button>
 {showContext && <div id="context-fields" className="context-fields">{([['relationship', 'Relationship', 'e.g. Classmates'], ['setting', 'Setting', 'e.g. Group chat']] as const).map(([key, label, placeholder]) => <label key={key}>{label}<input value={contextInfo[key]} placeholder={placeholder} onChange={e => setContextInfo(prev => ({ ...prev, [key]: e.target.value }))} /></label>)}<p>The engine uses these two fields as context cues. The preview is a formatting aid; final parsing happens in the backend.</p></div>}
 </div><aside className="sample-library"><p className="eyebrow">A PLACE TO START</p><h3>Try a conversation</h3><p>Explore a case, then make it your own.</p>{examples.length ? examples.slice(0, 4).map((ex, i) => <button disabled={isLoading} key={ex.id} onClick={() => { onSelectExample(ex); setView('edit'); }}><span className="sample-index">0{i + 1}</span><span><strong>{ex.title.split(' (')[0]}</strong><small>{ex.relationship}</small></span><ArrowRight size={15} /></button>) : <p className="sample-unavailable">Examples will appear when the local engine is connected.</p>}<div className="review-principle"><span>REVIEWER’S NOTE</span><p>A flagged message is a starting point for a closer look. Read the replies before drawing a conclusion.</p></div></aside></div>
 {error && <div className="editor-error" role="alert"><AlertCircle size={18} /><span>{error}</span></div>}
 <div className="editor-actions"><p>Processed by your configured analysis server.<br /><span>Current engine: conversational rules.</span></p><div><button className="clear-action" onClick={onClear} disabled={isLoading || !conversationText}><RotateCcw size={15} />Clear</button><button id="analyze-conversation-btn" className="primary-action" onClick={onAnalyze} disabled={isLoading || !conversationText.trim()}>{isLoading ? 'Reviewing conversation…' : 'Review conversation'}<ArrowRight size={17} /></button></div></div>
 </section>;
};
