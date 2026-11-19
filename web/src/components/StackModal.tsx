'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ProblemOpportunity, TechStackSelection } from '@/types';
import { X, Layers, Sparkles, Check, Cpu, Database, LayoutGrid, Terminal } from 'lucide-react';

interface StackModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: ProblemOpportunity | null;
  onConfirmBuild: (opportunity: ProblemOpportunity, stack: TechStackSelection) => Promise<void>;
}

export function StackModal({ isOpen, onClose, opportunity, onConfirmBuild }: StackModalProps) {
  const [frontend, setFrontend] = useState('React 18 + Tailwind CSS');
  const [backend, setBackend] = useState('FastAPI Async (Python 3.11)');
  const [database, setDatabase] = useState('PostgreSQL + SQLAlchemy 2.0 Async');
  const [architecture, setArchitecture] = useState('Layered Modular Monolith');
  const [customNotes, setCustomNotes] = useState('');
  const [isBuilding, setIsBuilding] = useState(false);

  if (!isOpen || !opportunity) return null;

  const stackOptions = {
    frontend: [
      { id: 'Next.js 14 App Router + Tailwind', name: 'Next.js 14 App Router', desc: 'Modern SSR & React Server Components' },
      { id: 'React 18 + Tailwind CSS', name: 'React 18 + Tailwind', desc: 'Vite SPA with fast component rendering' },
      { id: 'Vue 3 + Vite + Tailwind', name: 'Vue 3 + Vite', desc: 'Reactive composition API SPA' },
      { id: 'Vanilla TypeScript + HTML5', name: 'Vanilla TS + HTML5', desc: 'Zero runtime dependency architecture' },
    ],
    backend: [
      { id: 'FastAPI Async (Python 3.11)', name: 'FastAPI Async', desc: 'High-performance Python with OpenAPI' },
      { id: 'Node.js + Express (TypeScript)', name: 'Express (TypeScript)', desc: 'Ubiquitous JavaScript backend runtime' },
      { id: 'Go (Fiber / Gin Engine)', name: 'Go (Fiber Engine)', desc: 'Ultra-low latency compiled backend' },
      { id: 'Django REST Framework (Python)', name: 'Django REST / Ninja', desc: 'Batteries-included admin & ORM' },
    ],
    database: [
      { id: 'PostgreSQL + SQLAlchemy 2.0 Async', name: 'PostgreSQL Async', desc: 'Robust ACID relational database' },
      { id: 'SQLite with WAL Mode', name: 'SQLite (WAL Mode)', desc: 'Zero config embedded local database' },
      { id: 'Supabase (PostgreSQL + Realtime)', name: 'Supabase Realtime', desc: 'Hosted Postgres with Auth and Edge APIs' },
      { id: 'MongoDB + Motor Async', name: 'MongoDB Document', desc: 'Schema-flexible NoSQL JSON documents' },
    ],
    architecture: [
      { id: 'Layered Modular Monolith', name: 'Modular Monolith', desc: 'Clean separation with zero devops overhead' },
      { id: 'Clean / Hexagonal Architecture', name: 'Hexagonal / Ports', desc: 'Strict domain decoupling from frameworks' },
      { id: 'Event-Driven Microservices', name: 'Event-Driven', desc: 'Asynchronous event bus and decoupled services' },
    ],
  };

  const handleConfirm = async () => {
    setIsBuilding(true);
    try {
      await onConfirmBuild(opportunity, {
        frontend,
        backend,
        database,
        architecture,
        customNotes,
      });
      onClose();
    } catch (err) {
      console.error('Build failure:', err);
    } finally {
      setIsBuilding(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 8 }}
          transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
          className="relative flex h-full max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-border-subtle bg-[#090d16] shadow-2xl shadow-black"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border-subtle px-6 py-4 bg-[#0d1322]">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 border border-brand-500/30">
                  Visual Stack Customizer
                </span>
                <h3 className="text-sm font-bold text-white">Target: {opportunity.title}</h3>
              </div>
              <p className="mt-1 text-xs text-slate-400">
                Choose the technical foundations and custom requirements before generating the codebase blueprint.
              </p>
            </div>
            <button
              onClick={onClose}
              className="btn-press rounded-lg p-1.5 text-slate-400 hover:bg-surface-200 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Frontend selector */}
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200 mb-2.5">
                <LayoutGrid className="h-4 w-4 text-brand-400" />
                <span>Frontend Technology</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {stackOptions.frontend.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setFrontend(opt.id)}
                    className={`btn-press flex items-start justify-between rounded-xl border p-3 text-left transition-all ${
                      frontend === opt.id
                        ? 'border-brand-500 bg-brand-500/10 shadow-sm'
                        : 'border-border-subtle bg-surface-300/40 hover:bg-surface-200/50'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-white">{opt.name}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{opt.desc}</div>
                    </div>
                    {frontend === opt.id && <Check className="h-4 w-4 text-brand-400 shrink-0" />}
                  </button>
                ))}
              </div>
            </div>

            {/* Backend selector */}
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200 mb-2.5">
                <Cpu className="h-4 w-4 text-accent-emerald" />
                <span>Backend Framework</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {stackOptions.backend.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setBackend(opt.id)}
                    className={`btn-press flex items-start justify-between rounded-xl border p-3 text-left transition-all ${
                      backend === opt.id
                        ? 'border-accent-emerald bg-accent-emerald/10 shadow-sm'
                        : 'border-border-subtle bg-surface-300/40 hover:bg-surface-200/50'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-white">{opt.name}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{opt.desc}</div>
                    </div>
                    {backend === opt.id && <Check className="h-4 w-4 text-accent-emerald shrink-0" />}
                  </button>
                ))}
              </div>
            </div>

            {/* Database selector */}
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200 mb-2.5">
                <Database className="h-4 w-4 text-accent-cyan" />
                <span>Persistence & Database</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {stackOptions.database.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setDatabase(opt.id)}
                    className={`btn-press flex items-start justify-between rounded-xl border p-3 text-left transition-all ${
                      database === opt.id
                        ? 'border-accent-cyan bg-accent-cyan/10 shadow-sm'
                        : 'border-border-subtle bg-surface-300/40 hover:bg-surface-200/50'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-white">{opt.name}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{opt.desc}</div>
                    </div>
                    {database === opt.id && <Check className="h-4 w-4 text-accent-cyan shrink-0" />}
                  </button>
                ))}
              </div>
            </div>

            {/* Architecture selector */}
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200 mb-2.5">
                <Terminal className="h-4 w-4 text-accent-purple" />
                <span>Architecture Pattern</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {stackOptions.architecture.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setArchitecture(opt.id)}
                    className={`btn-press flex items-start justify-between rounded-xl border p-3 text-left transition-all ${
                      architecture === opt.id
                        ? 'border-accent-purple bg-accent-purple/10 shadow-sm'
                        : 'border-border-subtle bg-surface-300/40 hover:bg-surface-200/50'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold text-white">{opt.name}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{opt.desc}</div>
                    </div>
                    {architecture === opt.id && <Check className="h-4 w-4 text-accent-purple shrink-0" />}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Notes / Instructions */}
            <div>
              <label className="block text-xs font-bold text-slate-200 mb-1.5">
                Custom Requirements & Feature Directives
              </label>
              <textarea
                value={customNotes}
                onChange={(e) => setCustomNotes(e.target.value)}
                placeholder="e.g. Include Stripe subscription billing, mobile-responsive layout, PDF reporting export, role-based access control, barcode scanner integration..."
                rows={3}
                className="w-full rounded-xl border border-border-subtle bg-surface-400/90 p-3 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between border-t border-border-subtle px-6 py-4 bg-[#0d1322]">
            <div className="text-xs text-slate-400">
              Selected: <span className="font-semibold text-slate-200">{frontend.split('+')[0]}</span> + <span className="font-semibold text-slate-200">{backend.split('(')[0]}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={onClose}
                className="btn-press rounded-xl px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={isBuilding}
                className="btn-press flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-accent-purple px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-brand-500/25 hover:from-brand-500 hover:to-accent-purple/90 disabled:opacity-50"
              >
                {isBuilding ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Synthesizing Custom Blueprint...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Confirm & Generate Custom Blueprint ⚡</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
