'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ProblemOpportunity, ChatMessage } from '@/types';
import { api } from '@/lib/api';
import { Bot, Send, X, Sparkles, RefreshCw, ChevronRight } from 'lucide-react';

interface RefinementDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string | null;
  currentOpportunities: ProblemOpportunity[];
  onOpportunitiesUpdated: (newOpportunities: ProblemOpportunity[]) => void;
}

export function RefinementDrawer({
  isOpen,
  onClose,
  sessionId,
  currentOpportunities,
  onOpportunitiesUpdated,
}: RefinementDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      role: 'assistant',
      content:
        'Hello! Review the 4 proposals on screen. If they are not what you envision—or if you need different domains, target audiences, or technical constraints—tell me what you want to change.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const streamEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || isLoading) return;

    setInput('');
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setIsLoading(true);

    try {
      const historyPayload = newHistory.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await api.refineOpportunities(
        text,
        sessionId,
        historyPayload,
        currentOpportunities
      );

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content:
          res.message ||
          'I have refined the opportunity candidates according to your feedback. Notice the refreshed grid on your main screen!',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
      if (res.opportunities && res.opportunities.length > 0) {
        onOpportunitiesUpdated(res.opportunities);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error refining opportunities: ${err.message || 'Server error. Please retry.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPills = [
    { label: '⚡ Solo / Weekend MVP', prompt: 'I want ideas tailored for a Solo Developer or Weekend MVP project with low operational complexity.' },
    { label: '🏢 Enterprise B2B SaaS', prompt: 'Make these B2B SaaS ideas targeting enterprise operations, compliance, or finance workflows.' },
    { label: '📴 Offline / Mobile', prompt: 'Pivot these to mobile-first or offline-first field applications for users with intermittent internet.' },
    { label: '🔒 Privacy / Local-First', prompt: 'Focus on privacy-first developer tools with zero external telemetry and local-only storage.' },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Drawer container with Emil Kowalski ease-drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.28, ease: [0.32, 0.72, 0, 1] }}
            className="relative flex h-full w-full max-w-lg flex-col border-l border-border-subtle bg-[#090d16] shadow-2xl shadow-black"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4 bg-[#0d1322]">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/20 text-brand-300 border border-brand-500/30">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">AI Opportunity Refinement</h3>
                  <p className="text-[11px] text-slate-400">Converse to pivot domain, target audience, or complexity</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="btn-press rounded-lg p-1.5 text-slate-400 hover:bg-surface-200 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Quick Pills */}
            <div className="border-b border-border-subtle bg-surface-400/40 px-4 py-2.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Quick Pivots</span>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {quickPills.map((pill, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(pill.prompt)}
                    disabled={isLoading}
                    className="btn-press rounded-full border border-border-subtle bg-surface-300/80 px-2.5 py-1 text-[11px] font-medium text-slate-300 hover:border-brand-500/50 hover:bg-surface-200 disabled:opacity-50"
                  >
                    {pill.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {m.role === 'assistant' && (
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-600/20 text-brand-400 border border-brand-500/30">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'border border-border-subtle bg-surface-300 text-slate-200'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.content}</p>
                    <span className="mt-1.5 block text-[10px] opacity-60 text-right">{m.timestamp}</span>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3 items-center text-xs text-brand-300">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-600/20 border border-brand-500/30">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-brand-400" />
                  </div>
                  <span>Synthesizing new tailored opportunities...</span>
                </div>
              )}
              <div ref={streamEndRef} />
            </div>

            {/* Input Bar */}
            <div className="border-t border-border-subtle p-4 bg-[#0c121e]">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="e.g. Reject all, give me solo-dev ideas in healthcare..."
                  disabled={isLoading}
                  className="flex-1 rounded-xl border border-border-subtle bg-surface-400/90 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="btn-press flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-md shadow-brand-500/25 hover:bg-brand-500 disabled:opacity-40"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
