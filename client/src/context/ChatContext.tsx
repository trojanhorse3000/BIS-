import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import type { ChatMessage } from '../types';
import { postQuery } from '../services/api';

interface ChatContextType {
  messages: ChatMessage[];
  isStreaming: boolean;
  sendMessage: (query: string, lang?: string) => Promise<void>;
  clearChat: () => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
}

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: `Hi! 👋 I'm **ManakSetu**, your BIS regulatory assistant.

I can help you with:
- 🔍 **Standards lookup** — find any Indian Standard (IS number, title, scope)
- 📋 **QCO checks** — which products require compulsory certification
- ✨ **HUID verification** — hallmarking reference for gold & silver
- 🌐 **HS code crosswalk** — map customs codes to applicable Indian Standards

You can ask in English or हिंदी. Try one of the suggestions below, or type your own question!`,
  timestamp: new Date(),
};

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef(false);
  const streamIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopStreaming = useCallback(() => {
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
      streamIntervalRef.current = null;
    }
  }, []);

  const sendMessage = useCallback(async (query: string, lang = 'en') => {
    if (!query.trim() || isStreaming) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    abortRef.current = false;

    const assistantId = `assistant-${Date.now()}`;
    const placeholder: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    setMessages(prev => [...prev, placeholder]);

    try {
      const data = await postQuery(query, lang);
      if (abortRef.current) return;

      const fullText = data.answer || 'No answer generated.';
      let index = 0;
      const chunkSize = 3; // characters per tick

      streamIntervalRef.current = setInterval(() => {
        if (abortRef.current || index >= fullText.length) {
          stopStreaming();
          // Final message with full content and metadata
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? {
                    ...m,
                    content: fullText,
                    isStreaming: false,
                    intent: data.intent,
                    citations: data.citations,
                    verified: data.verified,
                    latency_ms: data.latency_ms,
                  }
                : m
            )
          );
          setIsStreaming(false);
          return;
        }

        index = Math.min(index + chunkSize, fullText.length);
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId ? { ...m, content: fullText.slice(0, index) } : m
          )
        );
      }, 12); // ~1000ms / (chunkSize/12ms) ≈ 27 chars/sec typing speed
    } catch (err: unknown) {
      if (abortRef.current) return;
      stopStreaming();
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response';
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? { ...m, content: `⚠️ ${errorMessage}`, isStreaming: false }
            : m
        )
      );
      setIsStreaming(false);
    }
  }, [isStreaming, stopStreaming]);

  const clearChat = useCallback(() => {
    stopStreaming();
    abortRef.current = true;
    setMessages([]);
    setIsStreaming(false);
  }, [stopStreaming]);

  return (
    <ChatContext.Provider value={{ messages, isStreaming, sendMessage, clearChat }}>
      {children}
    </ChatContext.Provider>
  );
}
