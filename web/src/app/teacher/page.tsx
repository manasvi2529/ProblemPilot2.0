'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Project, TeacherExplanation } from '@/types';
import { usePreferences } from '@/lib/preferences-context';
import {
  GraduationCap,
  Sparkles,
  BookOpen,
  Cpu,
  ShieldAlert,
  CheckCircle,
  HelpCircle,
  Copy,
  Check,
  Volume2,
  ArrowRight,
  Code,
  Layers,
  Flame,
} from 'lucide-react';

export default function TeacherPage() {
  const { speak } = usePreferences();

  const [topic, setTopic] = useState('FastAPI Async Coroutines');
  const [level, setLevel] = useState('interview_prep');
  const [selectedProjectId, setSelectedProjectId] = useState('global');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState<TeacherExplanation | null>(null);
  const [copiedQuote, setCopiedQuote] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProjects() {
      try {
        const list = await api.listProjects();
        setProjects(list);
      } catch (err) {
        console.debug('Failed to fetch projects for teacher:', err);
      }
    }
    loadProjects();
  }, []);

  const handleExplain = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.teachConcept(selectedProjectId, topic.trim(), level);
      setExplanation(res.explanation);
    } catch (err: any) {
      setError(err.message || 'Failed to generate explanation');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyInterviewQuote = (quote: string) => {
    navigator.clipboard.writeText(quote);
    setCopiedQuote(true);
    setTimeout(() => setCopiedQuote(false), 2000);
  };

  const quickPicks = [
    'FastAPI Async Coroutines',
    'Pydantic V2 Schema Validation',
    'SQLAlchemy Connection Pools',
    'Reverse Proxy & CORS Bypassing',
    'JWT Authentication & OAuth 2.0',
    'Database Indexing & N+1 Queries',
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 border border-brand-500/30">
            SYSTEM DESIGN & MENTORSHIP
          </span>
          <span className="text-xs text-slate-500 font-mono">Pedagogy Engine v2.0</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-white mt-1">
          AI Teacher & Placement Interview Mentor
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-slate-300">
          Deconstruct why design patterns and libraries exist, dive into under-the-hood engine mechanics,
          and practice articulate answers for FAANG and high-scale startup engineering interviews.
        </p>
      </div>

      {/* Inquiry Form Card */}
      <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 shadow-xl">
        <form onSubmit={handleExplain} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Concept, Pattern, or Decision
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. FastAPI Async Coroutines, Pydantic Schema Validation, SQLAlchemy Connection Pools"
              className="w-full rounded-xl border border-border-subtle bg-surface-400 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
              required
            />
          </div>

          {/* Quick Suggestions */}
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-[11px] font-medium text-slate-400 mr-1 flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-brand-400" />
              Suggested:
            </span>
            {quickPicks.map((pick) => (
              <button
                key={pick}
                type="button"
                onClick={() => setTopic(pick)}
                className={`btn-press rounded-lg px-2.5 py-1 text-[11px] font-medium border transition-colors ${
                  topic === pick
                    ? 'border-brand-500/50 bg-brand-500/20 text-brand-300'
                    : 'border-border-subtle bg-surface-400/80 text-slate-300 hover:text-white hover:bg-surface-400'
                }`}
              >
                {pick}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Explanation Tier
              </label>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3 py-2 text-xs font-semibold text-white focus:outline-none focus:border-brand-500"
              >
                <option value="interview_prep">🎓 Placement Interview Preparation (High Impact)</option>
                <option value="advanced">⚡ Advanced Architecture & System Trade-offs</option>
                <option value="intermediate">🛠️ Intermediate Full-Stack Implementation</option>
                <option value="beginner">🌱 Beginner Fundamentals & Mental Models</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Project Code Grounding
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3 py-2 text-xs font-semibold text-white focus:outline-none focus:border-brand-500"
              >
                <option value="global">🌐 General Full-Stack System Design (No Specific Repo)</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    📁 {p.title || p.name} ({p.id.slice(0, 8)})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between">
            <button
              type="submit"
              disabled={loading}
              className="btn-press flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-accent-purple px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-brand-500/20 hover:from-brand-500 hover:to-accent-purple/90 disabled:opacity-50 transition-all"
            >
              {loading ? (
                <>
                  <div className="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Synthesizing Pedagogical Breakdown...</span>
                </>
              ) : (
                <>
                  <GraduationCap className="h-4 w-4" />
                  <span>Explain Concept &rarr;</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error alert */}
      {error && (
        <div className="rounded-xl border border-accent-rose/30 bg-accent-rose/10 p-4 text-xs text-accent-rose flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Explanation Results Display */}
      {explanation && (
        <div className="space-y-6 animate-fadeIn">
          {/* Main Hero Summary Card */}
          <div className="rounded-2xl border border-border-subtle bg-surface-300/90 p-6 shadow-xl relative overflow-hidden">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 uppercase">
                    Tier: {explanation.level || level}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Topic: {explanation.topic}
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-black text-white">
                  {explanation.topic}
                </h2>
              </div>

              {/* TTS Listen Button */}
              <button
                onClick={() =>
                  speak(
                    `${explanation.topic}. ${explanation.summary}. In an interview, explain: ${
                      explanation.interview_explanation || ''
                    }`
                  )
                }
                className="btn-press flex items-center gap-1.5 rounded-xl border border-border-subtle bg-surface-400/80 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:text-white hover:bg-surface-400 transition-colors shrink-0"
                title="Listen via Speech Synthesis"
              >
                <Volume2 className="h-3.5 w-3.5 text-brand-400" />
                <span>Listen (TTS)</span>
              </button>
            </div>

            <p className="mt-4 text-sm text-slate-200 leading-relaxed font-sans">
              {explanation.summary}
            </p>

            {/* Mental Model */}
            {explanation.mental_model && (
              <div className="mt-4 rounded-xl border border-accent-cyan/30 bg-accent-cyan/10 p-4">
                <div className="flex items-center gap-2 text-xs font-bold text-accent-cyan uppercase tracking-wider mb-1">
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Intuitive Mental Model</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {explanation.mental_model}
                </p>
              </div>
            )}
          </div>

          {/* Interview Golden Quote Card */}
          {explanation.interview_explanation && (
            <div className="rounded-2xl border border-brand-500/40 bg-gradient-to-br from-brand-950/40 via-surface-300/90 to-surface-300/80 p-6 shadow-xl relative">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Flame className="h-4 w-4 text-amber-400" />
                  <span className="text-xs font-black uppercase tracking-wider text-amber-300">
                    How to Explain in a Placement Interview
                  </span>
                </div>
                <button
                  onClick={() => handleCopyInterviewQuote(explanation.interview_explanation!)}
                  className="btn-press flex items-center gap-1 rounded-lg border border-brand-500/30 bg-brand-500/10 px-2.5 py-1 text-[11px] font-semibold text-brand-300 hover:bg-brand-500/20"
                >
                  {copiedQuote ? (
                    <>
                      <Check className="h-3 w-3 text-accent-emerald" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy Answer</span>
                    </>
                  )}
                </button>
              </div>

              <blockquote className="rounded-xl border-l-4 border-amber-400 bg-black/40 p-4 text-sm text-amber-100 font-sans italic leading-relaxed">
                &ldquo;{explanation.interview_explanation}&rdquo;
              </blockquote>
            </div>
          )}

          {/* Under The Hood Mechanics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {explanation.under_the_hood && (
              <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-accent-purple">
                  <Cpu className="h-4 w-4" />
                  <span>How It Operates Under the Hood</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {explanation.under_the_hood}
                </p>
              </div>
            )}

            {explanation.how_it_works_here && (
              <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-400">
                  <Code className="h-4 w-4" />
                  <span>Implementation Architecture</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {explanation.how_it_works_here}
                </p>
              </div>
            )}
          </div>

          {/* Trade-offs & Alternatives */}
          {explanation.alternatives_and_tradeoffs && explanation.alternatives_and_tradeoffs.length > 0 && (
            <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
                <Layers className="h-4 w-4 text-accent-cyan" />
                <span>Alternatives Evaluated & Systems Trade-offs</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {explanation.alternatives_and_tradeoffs.map((item: any, idx) => {
                  const alt = typeof item === 'object' && item !== null ? (item.alternative || item.name || 'Alternative') : String(item);
                  const trade = typeof item === 'object' && item !== null ? (item.tradeoff || item.description || '') : '';
                  return (
                    <div key={idx} className="rounded-xl border border-border-subtle bg-surface-400/80 p-3.5">
                      <div className="text-xs font-bold text-accent-cyan">{alt}</div>
                      {trade && <div className="text-xs text-slate-300 mt-1">{trade}</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Common Pitfalls & Practical Exercises */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {explanation.common_pitfalls && explanation.common_pitfalls.length > 0 && (
              <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-accent-rose">
                  <ShieldAlert className="h-4 w-4" />
                  <span>Common Pitfalls & Failure Modes</span>
                </div>
                <ul className="space-y-2">
                  {explanation.common_pitfalls.map((pitfall: any, idx) => {
                    const isObj = typeof pitfall === 'object' && pitfall !== null;
                    const mistake = isObj ? (pitfall.mistake || pitfall.pitfall || pitfall.title || '') : '';
                    const avoidance = isObj ? (pitfall.avoidance || pitfall.solution || pitfall.fix || pitfall.description || '') : '';

                    return (
                      <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="text-accent-rose mt-0.5">&bull;</span>
                        {isObj ? (
                          <div>
                            {mistake && <span className="font-semibold text-rose-300">{mistake}: </span>}
                            <span>{avoidance || JSON.stringify(pitfall)}</span>
                          </div>
                        ) : (
                          <span>{String(pitfall)}</span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {explanation.practical_exercises && explanation.practical_exercises.length > 0 && (
              <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-accent-emerald">
                  <CheckCircle className="h-4 w-4" />
                  <span>Practical Challenges & Code Exercises</span>
                </div>
                <div className="space-y-2.5">
                  {explanation.practical_exercises.map((ex: any, idx) => {
                    const exercise = typeof ex === 'object' && ex !== null ? (ex.exercise || ex.title || ex.challenge || JSON.stringify(ex)) : String(ex);
                    const hint = typeof ex === 'object' && ex !== null ? (ex.hint || ex.solution || '') : '';

                    return (
                      <div key={idx} className="rounded-xl border border-border-subtle bg-surface-400/80 p-3">
                        <div className="text-xs font-bold text-white">{exercise}</div>
                        {hint && (
                          <div className="text-[11px] text-slate-400 mt-1">
                            <strong className="text-accent-emerald">Hint:</strong> {hint}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* How to test & What to learn next */}
          {(explanation.how_to_test || (explanation.what_to_learn_next && explanation.what_to_learn_next.length > 0)) && (
            <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-4">
              {explanation.how_to_test && (
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400">Testing Strategy</span>
                  <p className="text-xs text-slate-300 mt-1 font-mono bg-black/40 p-3 rounded-lg border border-border-subtle">
                    {explanation.how_to_test}
                  </p>
                </div>
              )}

              {explanation.what_to_learn_next && explanation.what_to_learn_next.length > 0 && (
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400">Recommended Next Topics</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {explanation.what_to_learn_next.map((nxt: any, idx) => {
                      const label = typeof nxt === 'object' && nxt !== null
                        ? (nxt.topic || nxt.title || nxt.name || JSON.stringify(nxt))
                        : String(nxt);
                      return (
                        <button
                          key={idx}
                          onClick={() => {
                            setTopic(label);
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                          }}
                          className="btn-press flex items-center gap-1.5 rounded-lg border border-brand-500/30 bg-brand-500/10 px-3 py-1.5 text-xs text-brand-300 hover:bg-brand-500/20"
                        >
                          <span>{label}</span>
                          <ArrowRight className="h-3 w-3" />
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
