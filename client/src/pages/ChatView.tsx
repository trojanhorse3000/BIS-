import { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat } from '../context/ChatContext';
import { Sparkles, User, CheckCircle2, Clock, Bot, Send } from 'lucide-react';
import type { ChatMessage, Citation, IntentData } from '../types';

function MarkdownText({ children }: { children: string }) {
  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-base font-bold text-ink mt-3 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-sm font-bold text-ink mt-2.5 mb-1.5">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold text-ink mt-2 mb-1">{children}</h3>,
          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="mb-2 space-y-1 list-disc list-inside">{children}</ul>,
          ol: ({ children }) => <ol className="mb-2 space-y-1 list-decimal list-inside">{children}</ol>,
          li: ({ children }) => <li className="text-sm">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline text-sm">
              {children}
            </a>
          ),
          code: ({ children, className, ...props }) => {
            const isBlock = className?.includes('language-');
            return isBlock ? (
              <code className={`block bg-bg-card text-accent text-xs rounded-lg px-3 py-2 my-2 overflow-x-auto font-mono ${className}`} {...props}>
                {children}
              </code>
            ) : (
              <code className="bg-bg-card text-accent text-xs px-1.5 py-0.5 rounded font-mono" {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => <pre className="mb-2">{children}</pre>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-accent/40 pl-3 py-1 my-2 text-muted text-sm italic">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="border-border my-3" />,
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="text-xs border-collapse w-full">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-border bg-bg-card px-2 py-1.5 text-left font-semibold text-muted">{children}</th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-2 py-1.5 text-ink">{children}</td>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1">
      <span className="w-1.5 h-1.5 rounded-full bg-accent/60 animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-accent/60 animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-accent/60 animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} message-enter`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 mt-1 border ${
        isUser
          ? 'bg-accent text-black border-accent'
          : 'bg-bg-card text-accent border-border'
      }`}>
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] sm:max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-accent text-black'
            : 'bg-bg-card border border-border text-ink'
        }`}>
          {isUser ? message.content : (
            message.isStreaming ? (
              <span className="streaming-cursor inline">{message.content}</span>
            ) : (
              <MarkdownText>{message.content}</MarkdownText>
            )
          )}
        </div>

        {/* Metadata */}
        {!isUser && (
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            {message.intent && <IntentBadge intent={message.intent} />}
            {message.verified && (
              <span className="inline-flex items-center gap-1 text-xs text-green font-mono">
                <CheckCircle2 size={12} /> VERIFIED
              </span>
            )}
            {message.latency_ms != null && (
              <span className="inline-flex items-center gap-1 text-xs text-muted font-mono">
                <Clock size={12} /> {message.latency_ms.toFixed(0)}ms
              </span>
            )}
            {message.isStreaming && (
              <span className="inline-flex items-center gap-1 text-xs text-accent font-mono">
                <Sparkles size={12} className="animate-pulse" />
                <TypingIndicator />
              </span>
            )}
          </div>
        )}

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && !message.isStreaming && (
          <Citations citations={message.citations} />
        )}
      </div>
    </div>
  );
}

function IntentBadge({ intent }: { intent: IntentData }) {
  const colorMap: Record<string, string> = {
    STANDARD_LOOKUP: 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
    CROSSWALK_LOOKUP: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30',
    HUID_VERIFICATION: 'bg-amber-500/20 text-amber-300 border border-amber-500/30',
    GENERAL_QUERY: 'bg-primary/5 text-ink-muted border border-primary/10',
    DOMAIN_REFUSAL_POLICY: 'bg-red-500/20 text-red-300 border border-red-500/30',
  };
  const color = colorMap[intent.intent] || 'bg-accent/20 text-accent border border-accent/30';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono ${color}`}>
      {intent.intent.replace(/_/g, ' ')}
      {intent.confidence != null && (
        <span className="ml-1 opacity-70">{(intent.confidence * 100).toFixed(0)}%</span>
      )}
    </span>
  );
}

function Citations({ citations }: { citations: Citation[] }) {
  return (
    <div className="mt-2 space-y-1">
      {citations.slice(0, 3).map((c, i) => (
        <a
          key={i}
          href={c.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-start gap-2 text-xs font-mono text-accent/80 hover:text-accent group cursor-pointer"
        >
          <span className="flex-shrink-0 w-4 h-4 rounded bg-accent/20 text-accent flex items-center justify-center text-[10px] font-bold mt-0.5">
            {i + 1}
          </span>
          <span className="group-hover:underline">
            <strong className="text-ink">{c.is_number}</strong> — {c.title}
          </span>
        </a>
      ))}
    </div>
  );
}

function Suggestions({ onSuggest }: { onSuggest: (text: string) => void }) {
  const suggestions = [
    { icon: '📋', text: 'What is IS 1293 standard for?', hint: '01_STD_LOOKUP' },
    { icon: '🔍', text: 'Which QCO applies to steel rods?', hint: '02_QCO_XWLK' },
    { icon: '✨', text: '22 क्यरेट सोनो का हॉलमार्क क्यो होतो है?', hint: '03_HUID_HI' },
    { icon: '📜', text: 'Tell me about BIS hallmarking scheme', hint: '04_GENERAL' },
  ];

  const info = [
    { icon: '📖', text: 'What is BIS and what does it do?', hint: 'ABOUT_BIS' },
    { icon: '🔢', text: 'What is an HS code?', hint: 'TRADE_HSC' },
    { icon: '📜', text: 'What is a QCO (Quality Control Order)?', hint: 'REG_QCO' },
    { icon: '💎', text: 'What is HUID hallmarking?', hint: 'GOLD_HUID' },
    { icon: '✅', text: 'What are ISI and CRS marks?', hint: 'CERT_MARKS' },
    { icon: '👤', text: 'Who needs BIS certification?', hint: 'COMP_LAW' },
  ];

  return (
    <div className="mt-4 mb-6 space-y-5">
      <div>
        <p className="text-xs font-mono text-muted uppercase tracking-widest mb-3">{'>'} Suggested queries</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="list" aria-label="Suggested queries">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggest(s.text)}
              className="text-left p-3 rounded-lg border border-border hover:border-accent/40 hover:bg-bg-hover transition-all duration-200 group cursor-pointer"
              role="listitem"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base">{s.icon}</span>
                <span className="text-[10px] font-mono text-accent/60">{s.hint}</span>
              </div>
              <p className="text-sm text-ink group-hover:text-accent transition-colors">
                {s.text}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs font-mono text-muted uppercase tracking-widest mb-3">{'>'} Learn the basics</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="list" aria-label="Learn questions">
          {info.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggest(s.text)}
              className="text-left p-3 rounded-lg border border-border hover:border-accent/40 hover:bg-bg-hover transition-all duration-200 group cursor-pointer"
              role="listitem"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base">{s.icon}</span>
                <span className="text-[10px] font-mono text-accent/60">{s.hint}</span>
              </div>
              <p className="text-sm text-ink group-hover:text-accent transition-colors">
                {s.text}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-col gap-3 px-4 py-6 max-w-3xl mx-auto w-full">
      {[1, 2].map(i => (
        <div key={i} className="flex gap-3">
          <div className="w-8 h-8 rounded bg-accent/20 flex-shrink-0 border border-accent/30" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-3/4 skeleton" />
            <div className="h-3 w-1/2 skeleton" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ChatView() {
  const { messages, isStreaming, sendMessage } = useChat();
  const [input, setInput] = useState('');
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const hasAutoScrolled = useRef(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  useEffect(() => {
    if (!hasAutoScrolled.current && messages.length === 1 && messages[0].id === 'welcome') {
      hasAutoScrolled.current = true;
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 150);
    }
  }, [messages]);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as string;
      setInput(detail);
      setTimeout(() => handleSubmit(), 100);
    };
    window.addEventListener('bis-suggest', handler);
    return () => window.removeEventListener('bis-suggest', handler);
  }, []);

  const handleSubmit = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    await sendMessage(text, lang);
  }, [input, isStreaming, lang, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  const showSuggestions = messages.length === 0 || (messages.length === 1 && messages[0].id === 'welcome');

  return (
    <div className="flex flex-col h-full bg-bg">
      {/* Header bar */}
      <div className="bg-bg-elevated border-b border-border px-4 py-3 flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center border border-accent/40">
          <Bot size={16} className="text-accent" />
        </div>
        <div>
          <div className="text-sm font-bold text-ink font-mono uppercase tracking-wider">ManakSetu</div>
          <div className="text-[10px] text-muted font-mono">BIS Regulatory Assistant</div>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
          <span className="text-[10px] font-mono text-muted">ONLINE</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full pb-8 px-4">
            <div className="w-14 h-14 rounded-lg bg-accent/10 flex items-center justify-center mb-4 border border-accent/20">
              <Bot className="text-accent" size={24} />
            </div>
            <h2 className="text-xl font-bold text-ink mb-2 uppercase tracking-wider font-mono">ManakSetu</h2>
            <p className="text-muted text-sm text-center max-w-sm mb-8">
              Ask about Indian Standards, QCO orders, hallmarking, or any BIS regulatory topic.
            </p>
            <Suggestions onSuggest={(text) => { window.dispatchEvent(new CustomEvent('bis-suggest', { detail: text })); }} />
          </div>
        ) : isStreaming && messages[messages.length - 1]?.role === 'assistant' && !messages[messages.length - 1]?.content ? (
          <LoadingState />
        ) : (
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {showSuggestions && (
              <Suggestions onSuggest={(text) => { window.dispatchEvent(new CustomEvent('bis-suggest', { detail: text })); }} />
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="border-t border-border bg-bg-elevated px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 bg-bg border border-border rounded-lg px-4 py-3 focus-within:border-accent/50 focus-within:ring-1 focus-within:ring-accent/20 transition-all">
            <span className="text-accent font-mono text-sm pt-1">$</span>
            <textarea
              ref={textareaRef}
              id="chat-input"
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask about BIS standards, QCO orders, or hallmarking…"
              rows={1}
              className="flex-1 bg-transparent text-sm text-ink placeholder:text-muted outline-none resize-none max-h-40 font-mono"
              disabled={isStreaming}
              aria-label="Type your message"
            />
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isStreaming}
              className="p-2 rounded-lg bg-accent text-black hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 flex-shrink-0 cursor-pointer"
              aria-label="Send message"
            >
              {isStreaming ? (
                <span className="animate-pulse">
                  <Sparkles size={16} />
                </span>
              ) : (
                <Send size={16} />
              )}
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 px-1">
            <p className="text-xs text-muted font-mono">
              {isStreaming ? '> processing…' : 'Enter to send · Shift+Enter new line'}
            </p>
            <select
              value={lang}
              onChange={e => setLang(e.target.value as 'en' | 'hi')}
              className="text-xs bg-bg text-muted border border-border rounded px-2 py-1 outline-none focus:border-accent/50 font-mono cursor-pointer"
              aria-label="Select language"
            >
              <option value="en">EN</option>
              <option value="hi">हिं</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
