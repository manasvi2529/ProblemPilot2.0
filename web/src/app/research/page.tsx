'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { ResearchSession, ProblemOpportunity } from '@/types';
import {
  Compass,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Globe,
  Sparkles,
  Layers,
  ArrowRight,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Users,
  Target,
  ShieldAlert,
  DollarSign,
  Award,
  Info,
} from 'lucide-react';

export default function ResearchPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [searchStep, setSearchStep] = useState(0);

  // Form inputs
  const [query, setQuery] = useState('');
  const [domain, setDomain] = useState('');
  const [geography, setGeography] = useState('');
  const [targetUsers, setTargetUsers] = useState('');

  // Active validation report
  const [activeReport, setActiveReport] = useState<any | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [currentProgressPct, setCurrentProgressPct] = useState<number>(0);
  const [currentStepMessage, setCurrentStepMessage] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [creatingProject, setCreatingProject] = useState(false);

  // Approval modal state for project conversion
  const [approvalModalOpp, setApprovalModalOpp] = useState<{
    reportId: string;
    oppIndex: number;
    title: string;
    proposedSolution: string;
    underservedNeed: string;
  } | null>(null);

  // Expanded session details
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);
  const [sessionDetails, setSessionDetails] = useState<Record<string, any>>({});
  const [loadingDetailId, setLoadingDetailId] = useState<string | null>(null);

  // Search providers diagnostics modal
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [diagnosticsData, setDiagnosticsData] = useState<any>(null);
  const [loadingDiag, setLoadingDiag] = useState(false);

  const openDiagnostics = async () => {
    setShowDiagnostics(true);
    setLoadingDiag(true);
    try {
      const data = await api.getResearchIntegrationStatus();
      setDiagnosticsData(data);
    } catch (err) {
      console.error('Failed to load integration diagnostics:', err);
    } finally {
      setLoadingDiag(false);
    }
  };

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const list = await api.listResearchSessions();
      setSessions(list);
    } catch (err) {
      console.error('Failed to load research sessions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const pollSessionUntilComplete = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    setIsSearching(true);
    let attempts = 0;
    const maxAttempts = 120; // 4 minutes max

    while (attempts < maxAttempts) {
      attempts++;
      try {
        const st = await api.getSessionStatus(sessionId);
        setCurrentProgressPct(st.progress_pct || 15);
        setCurrentStepMessage(st.step_message || 'Research in progress...');

        if (st.status === 'searching') setSearchStep(1);
        else if (st.status === 'extracting') setSearchStep(2);
        else if (st.status === 'analyzing') setSearchStep(3);
        else if (st.status === 'scoring') setSearchStep(4);

        if (st.status === 'completed' || st.has_report) {
          setSearchStep(5);
          setCurrentProgressPct(100);
          try {
            const repRes = await api.getSessionReport(sessionId);
            if (repRes && repRes.report) {
              setActiveReport(repRes.report);
            }
          } catch (rErr) {
            console.warn('Failed to fetch completed report:', rErr);
          }
          if (typeof window !== 'undefined') {
            localStorage.removeItem('active_research_session_id');
          }
          await loadSessions();
          break;
        } else if (st.status === 'failed') {
          setErrorMsg(st.error_message || 'Research session failed. Please check backend settings.');
          if (typeof window !== 'undefined') {
            localStorage.removeItem('active_research_session_id');
          }
          break;
        } else if (st.status === 'cancelled') {
          setErrorMsg('Research session was cancelled.');
          if (typeof window !== 'undefined') {
            localStorage.removeItem('active_research_session_id');
          }
          break;
        }
      } catch (pollErr) {
        console.warn('Polling error, retrying in 2s...', pollErr);
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
    setIsSearching(false);
  };

  useEffect(() => {
    loadSessions();
    if (typeof window !== 'undefined') {
      const savedSessId = localStorage.getItem('active_research_session_id');
      if (savedSessId) {
        pollSessionUntilComplete(savedSessId);
      }
    }
  }, []);

  const handleLaunchResearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || isSearching) return;

    setErrorMsg(null);
    setIsSearching(true);
    setSearchStep(1);
    setCurrentProgressPct(10);
    setCurrentStepMessage('Initiating research session...');

    try {
      const result = await api.validateOpportunity({
        query: query.trim(),
        domain: domain.trim(),
        geography: geography.trim(),
        target_users: targetUsers.trim(),
      });

      if (!result || !result.session) {
        throw new Error('Failed to create research session');
      }

      const sessId = result.session.id;
      if (typeof window !== 'undefined') {
        localStorage.setItem('active_research_session_id', sessId);
      }

      if (result.report) {
        // Immediate/synchronous result
        setActiveReport(result.report);
        setCurrentProgressPct(100);
        setSearchStep(5);
        if (typeof window !== 'undefined') {
          localStorage.removeItem('active_research_session_id');
        }
        setIsSearching(false);
        await loadSessions();
      } else {
        // Asynchronous polling
        await pollSessionUntilComplete(sessId);
      }
    } catch (err: any) {
      console.error('Opportunity validation failed:', err);
      setErrorMsg(err.message || 'Failed to complete research validation. Please check backend settings.');
      setIsSearching(false);
    }
  };

  const handleCancelActiveSession = async () => {
    if (!activeSessionId) return;
    try {
      await api.cancelResearchSession(activeSessionId);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('active_research_session_id');
      }
      setIsSearching(false);
      setErrorMsg('Research session cancelled.');
    } catch (err) {
      console.warn('Cancel error:', err);
    }
  };

  const toggleExpandSession = async (sessionId: string) => {
    if (expandedSessionId === sessionId) {
      setExpandedSessionId(null);
      return;
    }
    setExpandedSessionId(sessionId);
    if (!sessionDetails[sessionId]) {
      setLoadingDetailId(sessionId);
      try {
        const detail = await api.getResearchSession(sessionId);
        setSessionDetails((prev) => ({ ...prev, [sessionId]: detail }));
        try {
          const repRes = await api.getSessionReport(sessionId);
          if (repRes && repRes.report) {
            setSessionDetails((prev) => ({
              ...prev,
              [sessionId]: { ...prev[sessionId], full_report: repRes.report },
            }));
          }
        } catch {
          // Report may not exist for in-progress or legacy sessions
        }
      } catch (err) {
        console.error('Failed to load session details:', err);
      } finally {
        setLoadingDetailId(null);
      }
    }
  };

  const handleCreateProjectFromOpp = async (reportId: string, oppIndex: number = 0) => {
    setCreatingProject(true);
    try {
      const res = await api.convertReportToProject(reportId, {
        opportunity_index: oppIndex,
        approved: true,
      });
      if (res && res.project && res.project.id) {
        setApprovalModalOpp(null);
        router.push(`/projects/${res.project.id}`);
      }
    } catch (err: any) {
      console.error('Failed to convert opportunity to project:', err);
      alert(`Could not create project: ${err.message}`);
    } finally {
      setCreatingProject(false);
    }
  };

  const exampleQueries = [
    {
      q: 'AI-powered education for college students in India',
      d: 'Education & Career Tech',
      g: 'India',
      u: 'Undergraduate engineering & BCA students',
    },
    {
      q: 'Automated invoice reconciliation for small e-commerce sellers',
      d: 'Fintech & Retail',
      g: 'United States',
      u: 'Shopify / WooCommerce store owners',
    },
    {
      q: 'Real-time API latency debugging and anomaly alerts',
      d: 'Developer Tools',
      g: 'Global',
      u: 'Backend software engineers',
    },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* ── Top Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2.5">
            <Compass className="h-6 w-6 text-brand-400" />
            Live Research & Opportunity Validation Engine
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Discovers real-world problems from live web research, community discussions, and transparent multi-factor scoring.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          <button
            onClick={openDiagnostics}
            className="btn-press inline-flex items-center gap-2 rounded-xl bg-surface-300 hover:bg-surface-200 border border-brand-500/40 px-3.5 py-2 text-xs font-semibold text-brand-300 transition-colors"
          >
            <Globe className="h-3.5 w-3.5 text-accent-cyan" />
            <span>Search Providers</span>
          </button>
          <button
            onClick={loadSessions}
            disabled={isLoading}
            className="btn-press inline-flex items-center gap-2 rounded-xl bg-surface-300 hover:bg-surface-200 border border-border-subtle px-3.5 py-2 text-xs font-semibold text-slate-200 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Records</span>
          </button>
        </div>
      </div>

      {/* ── Research Input Hero Card ────────────────────────────────────────── */}
      <div className="rounded-2xl border border-brand-500/30 bg-gradient-to-br from-surface-300/90 via-surface-300/60 to-surface-400/40 p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-brand-500/20 border border-brand-500/40 px-3 py-1 text-xs font-bold text-brand-300 flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Natural-Language Opportunity Discovery</span>
            </span>
            <span className="text-xs text-slate-400">Zero static lists &bull; Live evidence only</span>
          </div>

          <form onSubmit={handleLaunchResearch} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                What problem area or opportunity do you want to research?
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. I want to find opportunities in AI-powered education for college students in India..."
                rows={3}
                required
                className="w-full rounded-xl bg-surface-400/80 border border-border-subtle p-3.5 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-all"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                  Domain / Industry (Optional)
                </label>
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="e.g. EdTech, Healthcare, FinTech"
                  className="w-full rounded-lg bg-surface-400/80 border border-border-subtle p-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                  Geography / Market (Optional)
                </label>
                <input
                  type="text"
                  value={geography}
                  onChange={(e) => setGeography(e.target.value)}
                  placeholder="e.g. India, US, Global"
                  className="w-full rounded-lg bg-surface-400/80 border border-border-subtle p-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                  Target Audience (Optional)
                </label>
                <input
                  type="text"
                  value={targetUsers}
                  onChange={(e) => setTargetUsers(e.target.value)}
                  placeholder="e.g. College students, DevOps leads"
                  className="w-full rounded-lg bg-surface-400/80 border border-border-subtle p-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 outline-none"
                />
              </div>
            </div>

            {/* Quick Suggestions */}
            <div className="flex items-center gap-2 flex-wrap pt-1">
              <span className="text-[11px] text-slate-400 font-medium">Try example:</span>
              {exampleQueries.map((ex, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuery(ex.q);
                    setDomain(ex.d);
                    setGeography(ex.g);
                    setTargetUsers(ex.u);
                  }}
                  className="rounded-lg bg-surface-400/60 hover:bg-surface-400 border border-border-subtle px-2.5 py-1 text-[11px] text-slate-300 hover:text-white transition-colors"
                >
                  {ex.q}
                </button>
              ))}
            </div>

            {errorMsg && (
              <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-3 text-xs text-red-300 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5 text-accent-cyan" />
                <span>Queries Google / Serper / Brave + Reddit &amp; HN Communities</span>
              </span>

              <button
                type="submit"
                disabled={isSearching || !query.trim()}
                className="btn-press inline-flex items-center gap-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-brand-500/25 transition-all"
              >
                {isSearching ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Investigating Topic...</span>
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" />
                    <span>Launch Live Research</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Live Progress Stepper & Progress Bar */}
          {isSearching && (
            <div className="rounded-xl bg-surface-400/90 border border-brand-500/30 p-4 space-y-3 mt-4 animate-fade-in">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand-300 flex items-center gap-2">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>{currentStepMessage || 'Live Research Pipeline in Progress...'}</span>
                </span>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-mono font-bold text-brand-400">{currentProgressPct}%</span>
                  <button
                    type="button"
                    onClick={handleCancelActiveSession}
                    className="text-[10px] text-red-400 hover:text-red-300 px-2 py-0.5 rounded border border-red-500/30 hover:border-red-500/60"
                  >
                    Cancel
                  </button>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-surface-300 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-brand-500 h-full rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${Math.max(5, Math.min(100, currentProgressPct))}%` }}
                />
              </div>

              <div className="grid grid-cols-5 gap-2 text-center text-[10px] font-semibold text-slate-400 pt-1">
                <div className={`p-1.5 rounded-lg border ${searchStep >= 1 ? 'border-brand-500/50 bg-brand-500/20 text-brand-200' : 'border-border-subtle'}`}>
                  1. Plan Query
                </div>
                <div className={`p-1.5 rounded-lg border ${searchStep >= 2 ? 'border-brand-500/50 bg-brand-500/20 text-brand-200' : 'border-border-subtle'}`}>
                  2. Search Web &amp; Forums
                </div>
                <div className={`p-1.5 rounded-lg border ${searchStep >= 3 ? 'border-brand-500/50 bg-brand-500/20 text-brand-200' : 'border-border-subtle'}`}>
                  3. Extract Citations
                </div>
                <div className={`p-1.5 rounded-lg border ${searchStep >= 4 ? 'border-brand-500/50 bg-brand-500/20 text-brand-200' : 'border-border-subtle'}`}>
                  4. Score Dimensions
                </div>
                <div className={`p-1.5 rounded-lg border ${searchStep >= 5 ? 'border-brand-500/50 bg-brand-500/20 text-brand-200' : 'border-border-subtle'}`}>
                  5. Synthesize Report
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Active 13-Section Structured Report Card ────────────────────────── */}
      {activeReport && (
        <div className="rounded-2xl border border-brand-500/40 bg-surface-300/90 p-6 shadow-2xl space-y-6 animate-fade-in">
          {/* Report Top Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border-subtle">
            <div>
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="rounded-full bg-accent-green/15 border border-accent-green/30 px-2.5 py-0.5 text-[10px] font-bold text-accent-green uppercase tracking-wider flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Validated Opportunity Report
                </span>

                {/* Phase 1.7 Canonical Search Mode Badge */}
                {activeReport.search_mode === 'live' || (activeReport.used_live_search && activeReport.search_mode !== 'curated_fallback') ? (
                  <span className="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1">
                    <Globe className="h-3 w-3" />
                    Live Web Research ({activeReport.search_provider || 'Authenticated Provider'})
                  </span>
                ) : activeReport.search_mode === 'mixed' ? (
                  <span className="rounded-full bg-amber-500/15 border border-amber-500/30 px-2.5 py-0.5 text-[10px] font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1">
                    <Globe className="h-3 w-3" />
                    Mixed Live &amp; Community
                  </span>
                ) : (
                  <span className="rounded-full bg-slate-500/20 border border-slate-500/40 px-2.5 py-0.5 text-[10px] font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1" title="Search credentials not configured. Operating in transparent curated simulation.">
                    <AlertTriangle className="h-3 w-3 text-amber-400" />
                    Curated Domain Simulation
                  </span>
                )}

                <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider border ${
                  activeReport.evidence_sufficiency === 'high'
                    ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
                    : activeReport.evidence_sufficiency === 'moderate'
                    ? 'bg-amber-500/15 border-amber-500/30 text-amber-300'
                    : 'bg-red-500/15 border-red-500/30 text-red-300'
                }`}>
                  Evidence Sufficiency: {activeReport.evidence_sufficiency}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {activeReport.search_provider ? `Provider: ${activeReport.search_provider}` : 'Multi-source'}
                </span>
              </div>
              <h2 className="text-xl font-black text-white">{activeReport.title}</h2>
            </div>

            <button
              onClick={() => handleCreateProjectFromOpp(activeReport.id, 0)}
              disabled={creatingProject}
              className="btn-press self-start sm:self-auto inline-flex items-center gap-2 rounded-xl bg-accent-green hover:bg-emerald-500 px-4 py-2 text-xs font-bold text-surface-500 shadow-md shadow-emerald-500/20 transition-all"
            >
              {creatingProject ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Creating Project...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Build This Project</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>

          {/* Section 1: Executive Summary */}
          <div className="rounded-xl bg-surface-400/60 p-4 border border-border-subtle space-y-1.5">
            <h3 className="text-xs font-bold text-brand-300 uppercase tracking-wider flex items-center gap-1.5">
              <Award className="h-3.5 w-3.5" />
              1. Executive Summary
            </h3>
            <p className="text-xs text-slate-200 leading-relaxed">
              {activeReport.executive_summary}
            </p>
          </div>

          {/* Section 2 & 3: Problem Landscape & Target Audience */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl bg-surface-400/50 p-4 border border-border-subtle space-y-2">
              <h3 className="text-xs font-bold text-accent-cyan uppercase tracking-wider flex items-center gap-1.5">
                <Target className="h-3.5 w-3.5" />
                2. Problem Landscape
              </h3>
              <p className="text-xs text-slate-300 font-semibold">
                {activeReport.problem_landscape?.core_conflict}
              </p>
              {activeReport.problem_landscape?.underlying_causes && (
                <ul className="text-[11px] text-slate-400 space-y-1 list-disc list-inside">
                  {activeReport.problem_landscape.underlying_causes.map((c: string, idx: number) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-xl bg-surface-400/50 p-4 border border-border-subtle space-y-2">
              <h3 className="text-xs font-bold text-brand-300 uppercase tracking-wider flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5" />
                3. Target Audience &amp; Segments
              </h3>
              <div className="text-xs text-slate-300 space-y-1">
                <div><span className="font-semibold text-white">Primary:</span> {activeReport.target_audience?.primary_segment}</div>
                <div><span className="font-semibold text-white">Early Adopters:</span> {activeReport.target_audience?.early_adopters}</div>
              </div>
              {activeReport.target_audience?.key_behaviors && (
                <ul className="text-[11px] text-slate-400 space-y-1 list-disc list-inside">
                  {activeReport.target_audience.key_behaviors.map((b: string, idx: number) => (
                    <li key={idx}>{b}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Section 4: Customer Pain Points */}
          {activeReport.customer_pain_points && activeReport.customer_pain_points.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                4. Customer Pain Points &amp; Recurring Frustrations
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {activeReport.customer_pain_points.map((p: any, idx: number) => (
                  <div key={idx} className="rounded-xl bg-surface-400/40 p-3.5 border border-border-subtle space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="rounded bg-red-500/20 text-red-300 px-2 py-0.5 text-[10px] font-bold">
                        {p.severity} Severity
                      </span>
                      <span className="text-[10px] text-slate-400">{p.frequency}</span>
                    </div>
                    <h5 className="text-xs font-bold text-white">{p.issue}</h5>
                    {p.evidence_quote && (
                      <p className="text-[11px] text-slate-400 italic">
                        &ldquo;{p.evidence_quote}&rdquo;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 5 & 6: Competitor Analysis & Verifiable Pricing */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <DollarSign className="h-3.5 w-3.5 text-accent-green" />
              5 &amp; 6. Competitor Analysis &amp; Pricing Models
            </h3>
            <div className="overflow-x-auto rounded-xl border border-border-subtle">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-surface-400/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-border-subtle">
                  <tr>
                    <th className="p-3">Competitor</th>
                    <th className="p-3">Positioning</th>
                    <th className="p-3">Strengths</th>
                    <th className="p-3">Weaknesses / Gaps</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle bg-surface-400/40">
                  {activeReport.competitor_analysis?.map((c: any, idx: number) => (
                    <tr key={idx} className="hover:bg-surface-400/60 transition-colors">
                      <td className="p-3 font-bold text-white">{c.name}</td>
                      <td className="p-3">{c.positioning}</td>
                      <td className="p-3 text-emerald-300">{c.strengths}</td>
                      <td className="p-3 text-red-300">{c.gap || c.weaknesses}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {activeReport.competitor_pricing?.pricing_notes && (
              <p className="text-[11px] text-slate-400 italic pt-1">
                Pricing Insight: {activeReport.competitor_pricing.pricing_notes}
              </p>
            )}
          </div>

          {/* Section 7: Market Trends */}
          {activeReport.market_trends && activeReport.market_trends.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="h-3.5 w-3.5 text-brand-400" />
                7. Market Trends &amp; Momentum
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {activeReport.market_trends.map((t: any, idx: number) => (
                  <div key={idx} className="rounded-xl bg-surface-400/40 p-3.5 border border-border-subtle space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{t.trend}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        t.status === 'emerging' ? 'bg-accent-cyan/20 text-accent-cyan' : 'bg-brand-500/20 text-brand-300'
                      }`}>
                        {t.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">{t.significance}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 8: Identified Opportunities */}
          {activeReport.identified_opportunities && activeReport.identified_opportunities.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-accent-green uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5" />
                8. Identified Opportunities &amp; Architecture Directives
              </h3>
              <div className="space-y-3">
                {activeReport.identified_opportunities.map((opp: any, idx: number) => (
                  <div
                    key={idx}
                    className="rounded-xl bg-surface-400/70 p-4 border border-brand-500/30 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                  >
                    <div className="space-y-1.5">
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <span>{opp.title}</span>
                      </h4>
                      <p className="text-xs text-slate-300">{opp.proposed_solution}</p>
                      <div className="text-[11px] text-slate-400">
                        <span className="text-amber-300 font-semibold">Underserved Need:</span> {opp.underserved_need}
                      </div>
                    </div>
                    <button
                      onClick={() => setApprovalModalOpp({
                        reportId: activeReport.id,
                        oppIndex: idx,
                        title: opp.title,
                        proposedSolution: opp.proposed_solution,
                        underservedNeed: opp.underserved_need,
                      })}
                      disabled={creatingProject}
                      className="btn-press shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 px-3.5 py-2 text-xs font-bold text-white shadow-md shadow-brand-500/20"
                    >
                      <span>Build Project</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 9: Opportunity Scores and Reasoning */}
          {activeReport.opportunity_scores && (
            <div className="rounded-xl bg-surface-400/60 p-4 border border-border-subtle space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="h-3.5 w-3.5 text-accent-green" />
                  9. Opportunity Scoring &amp; Multi-Factor Reasoning
                </h3>
                <span className="rounded-full bg-brand-500/20 border border-brand-500/30 px-3 py-0.5 text-xs font-bold text-brand-300">
                  Overall Score: {activeReport.opportunity_scores.overall_score} / 10
                </span>
              </div>

              {activeReport.opportunity_scores.dimensions && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                  {Object.entries(activeReport.opportunity_scores.dimensions).map(([dimKey, dimVal]: [string, any]) => (
                    <div key={dimKey} className="rounded-lg bg-surface-400/80 p-2.5 border border-border-subtle space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-semibold text-slate-300 capitalize">{dimKey.replace(/_/g, ' ')}</span>
                        <span className="font-mono font-bold text-brand-400">{dimVal.score}/10</span>
                      </div>
                      <div className="w-full bg-surface-300 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-brand-500 h-full rounded-full"
                          style={{ width: `${Math.min(100, (dimVal.score / 10) * 100)}%` }}
                        />
                      </div>
                      <p className="text-[10px] text-slate-400 line-clamp-2">{dimVal.explanation}</p>
                    </div>
                  ))}
                </div>
              )}

              {activeReport.opportunity_scores.disclaimer && (
                <p className="text-[10px] text-slate-400 italic pt-1 flex items-center gap-1">
                  <Info className="h-3 w-3 shrink-0" />
                  <span>{activeReport.opportunity_scores.disclaimer}</span>
                </p>
              )}
            </div>
          )}

          {/* Section 10 & 11: Risks, Mitigations & Recommendations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl bg-surface-400/50 p-4 border border-border-subtle space-y-2">
              <h3 className="text-xs font-bold text-red-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="h-3.5 w-3.5" />
                10. Risks &amp; Technical Limitations
              </h3>
              <div className="space-y-2">
                {activeReport.risks_and_limitations?.map((r: any, idx: number) => (
                  <div key={idx} className="text-xs space-y-0.5">
                    <div className="font-bold text-white flex items-center gap-1.5">
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface-300 text-slate-300 uppercase">{r.category}</span>
                      <span>{r.risk}</span>
                    </div>
                    <div className="text-[11px] text-emerald-300">Mitigation: {r.mitigation}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl bg-surface-400/50 p-4 border border-border-subtle space-y-2">
              <h3 className="text-xs font-bold text-accent-green uppercase tracking-wider flex items-center gap-1.5">
                <Target className="h-3.5 w-3.5" />
                11. Actionable Recommendations
              </h3>
              <div className="space-y-2">
                {activeReport.actionable_recommendations?.map((a: any, idx: number) => (
                  <div key={idx} className="text-xs space-y-0.5">
                    <div className="font-bold text-white flex items-center justify-between">
                      <span>{a.step}</span>
                      <span className="text-[10px] text-brand-300 font-mono">{a.timeline}</span>
                    </div>
                    <div className="text-[11px] text-slate-400">{a.action}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 12: Final Conclusion */}
          <div className="rounded-xl bg-surface-400/60 p-4 border border-border-subtle space-y-1">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              12. Final Conclusion &amp; Verdict
            </h3>
            <p className="text-xs text-slate-200 leading-relaxed font-semibold">
              {activeReport.final_conclusion}
            </p>
          </div>

          {/* Section 13: Clickable Sources & References */}
          {activeReport.sources && activeReport.sources.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5 text-accent-cyan" />
                13. Verified Sources &amp; References ({activeReport.sources.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {activeReport.sources.map((src: any, sIdx: number) => (
                  <a
                    key={sIdx}
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group rounded-xl bg-surface-400/40 p-3 border border-border-subtle hover:border-brand-500/40 hover:bg-surface-400/70 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-semibold text-brand-400 uppercase">
                            {src.publisher || 'Web Reference'}
                          </span>
                          {src.provider && (
                            <span className="px-1.5 py-0.2 rounded bg-surface-300 text-[9px] text-slate-300 border border-border-subtle uppercase">
                              {src.provider}
                            </span>
                          )}
                          <span className={`px-1.5 py-0.2 rounded text-[9px] font-semibold border ${
                            src.content_extracted
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                              : 'bg-slate-500/10 text-slate-400 border-slate-500/30'
                          }`}>
                            {src.content_extracted ? 'Full Text Extracted' : 'Snippet Only'}
                          </span>
                        </div>
                        <ExternalLink className="h-3 w-3 text-slate-500 group-hover:text-brand-300" />
                      </div>
                      <h6 className="text-xs font-bold text-slate-200 line-clamp-1 group-hover:text-brand-300">
                        {src.title || src.url}
                      </h6>
                      {src.supporting_passage ? (
                        <div className="mt-1.5 p-1.5 rounded bg-surface-500/60 border border-border-subtle/80 text-[11px] text-slate-300 italic">
                          <span className="text-brand-400 font-bold not-italic text-[10px] block mb-0.5">Supporting Passage:</span>
                          &ldquo;{src.supporting_passage}&rdquo;
                        </div>
                      ) : src.snippet ? (
                        <p className="mt-1 text-[11px] text-slate-400 line-clamp-2">
                          &ldquo;{src.snippet}&rdquo;
                        </p>
                      ) : null}
                    </div>
                    <div className="mt-2 pt-2 border-t border-border-subtle/60 flex items-center justify-between text-[10px] text-slate-500">
                      <span className="capitalize">{src.claim_type ? src.claim_type.replace(/_/g, ' ') : 'Verified source'}</span>
                      {src.publication_date && <span>{new Date(src.publication_date).toLocaleDateString()}</span>}
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Historical Research Sessions Log ───────────────────────────────── */}
      <div className="space-y-4 pt-4 border-t border-border-subtle">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Layers className="h-4 w-4 text-brand-400" />
          <span>Research Sessions Audit Trail ({sessions.length})</span>
        </h2>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-28 rounded-2xl border border-border-subtle bg-surface-300/40 animate-pulse" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-8 text-center text-xs text-slate-400">
            No previous research sessions recorded yet. Enter a topic above to launch your first live research pipeline.
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((sess) => {
              const isExpanded = expandedSessionId === sess.id;
              const details = sessionDetails[sess.id];
              const isLoadingDetails = loadingDetailId === sess.id;

              return (
                <div
                  key={sess.id}
                  className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 shadow-md transition-all hover:border-border-default"
                >
                  <div
                    onClick={() => toggleExpandSession(sess.id)}
                    className="flex items-start justify-between cursor-pointer select-none"
                  >
                    <div className="space-y-1.5 pr-4">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="rounded-full bg-brand-500/15 border border-brand-500/30 px-2.5 py-0.5 text-[10px] font-bold text-brand-300 uppercase tracking-wider">
                          Query
                        </span>
                        <span className="text-xs text-slate-400 font-mono">
                          {sess.created_at
                            ? new Date(sess.created_at).toLocaleString([], {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })
                            : 'Recent'}
                        </span>
                        {sess.used_live_search ? (
                          <span className="rounded bg-emerald-500/20 text-emerald-300 px-2 py-0.2 text-[10px] font-bold">
                            Live Web Search
                          </span>
                        ) : (
                          <span className="rounded bg-slate-500/20 text-slate-300 px-2 py-0.2 text-[10px] font-bold">
                            Community Sources
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-bold text-white">{sess.query}</h3>
                    </div>

                    <button className="btn-press p-2 rounded-xl bg-surface-400/80 text-slate-300 hover:text-white">
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 pt-3 border-t border-border-subtle space-y-4 animate-fade-in">
                      {isLoadingDetails ? (
                        <div className="p-6 text-center text-xs text-slate-400 animate-pulse">
                          Loading session sources and full report...
                        </div>
                      ) : (
                        <>
                          {details?.full_report && (
                            <button
                              onClick={() => {
                                setActiveReport(details.full_report);
                                window.scrollTo({ top: 300, behavior: 'smooth' });
                              }}
                              className="btn-press inline-flex items-center gap-2 rounded-lg bg-brand-600/30 hover:bg-brand-600/50 border border-brand-500/40 px-3 py-1.5 text-xs font-semibold text-brand-200"
                            >
                              <Award className="h-3.5 w-3.5" />
                              <span>View Full 13-Section Report in Viewer</span>
                            </button>
                          )}

                          {details?.sources && details.sources.length > 0 && (
                            <div className="space-y-2">
                              <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                                Sources Retrieved ({details.sources.length})
                              </h5>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {details.sources.slice(0, 6).map((src: any, sIdx: number) => (
                                  <a
                                    key={src.id || sIdx}
                                    href={src.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="rounded-lg bg-surface-400/40 p-2.5 border border-border-subtle hover:border-brand-500/40 transition-all flex items-center justify-between text-xs text-slate-300"
                                  >
                                    <span className="truncate pr-2">{src.title || src.url}</span>
                                    <ExternalLink className="h-3 w-3 shrink-0 text-slate-500" />
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Project Conversion Approval Modal ────────────────────────────── */}
      {approvalModalOpp && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full rounded-2xl bg-surface-300 border border-brand-500/50 p-6 shadow-2xl space-y-4 animate-scale-in">
            <div className="flex items-center gap-2 text-brand-400">
              <Sparkles className="h-5 w-5" />
              <h3 className="text-base font-bold text-white">Approve Project Creation</h3>
            </div>

            <p className="text-xs text-slate-300">
              You are approving the conversion of this validated research opportunity into a runnable software project:
            </p>

            <div className="rounded-xl bg-surface-400 p-3.5 border border-border-subtle space-y-2">
              <h4 className="text-xs font-bold text-white">{approvalModalOpp.title}</h4>
              <p className="text-[11px] text-slate-300">{approvalModalOpp.proposedSolution}</p>
              <div className="text-[10px] text-slate-400">
                <span className="text-amber-300 font-semibold">Need:</span> {approvalModalOpp.underservedNeed}
              </div>
            </div>

            <p className="text-[11px] text-slate-400">
              This will preserve the research report and pass its structured findings into the Blueprint Engine to scaffold and run the initial project.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setApprovalModalOpp(null)}
                disabled={creatingProject}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleCreateProjectFromOpp(approvalModalOpp.reportId, approvalModalOpp.oppIndex)}
                disabled={creatingProject}
                className="btn-press inline-flex items-center gap-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 px-5 py-2 text-xs font-bold text-white shadow-lg shadow-brand-500/25"
              >
                {creatingProject ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Scaffolding Project...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Approve &amp; Build Project</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* ── Search Providers Diagnostics Modal ───────────────────────────── */}
      {showDiagnostics && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-lg w-full rounded-2xl bg-surface-300 border border-brand-500/50 p-6 shadow-2xl space-y-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <div className="flex items-center gap-2 text-brand-400">
                <Globe className="h-5 w-5" />
                <h3 className="text-base font-bold text-white">Search Providers &amp; Connectivity</h3>
              </div>
              <button
                onClick={() => setShowDiagnostics(false)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg bg-surface-400"
              >
                Close
              </button>
            </div>

            {loadingDiag ? (
              <div className="py-8 flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
                <RefreshCw className="h-5 w-5 animate-spin text-brand-400" />
                <span>Checking provider configurations...</span>
              </div>
            ) : (
              <div className="space-y-4 text-xs">
                <div className="rounded-xl bg-surface-400/80 p-3.5 border border-border-subtle space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-300">Live Search Credentials Status:</span>
                    <span className={`px-2 py-0.5 rounded font-bold uppercase text-[10px] ${
                      diagnosticsData?.search?.configured
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    }`}>
                      {diagnosticsData?.search?.configured ? 'Active Credentials Configured' : 'Curated Fallback Simulation'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {diagnosticsData?.search?.message}
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Configured Search Adapters
                  </h4>
                  <div className="space-y-2">
                    {/* Serper */}
                    <div className="p-3 rounded-xl bg-surface-400/50 border border-border-subtle flex items-center justify-between">
                      <div>
                        <div className="font-bold text-white flex items-center gap-1.5">
                          <span>Serper.dev</span>
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-brand-500/20 text-brand-300">Primary Recommended</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Key: {diagnosticsData?.search?.diagnostics?.providers?.serper?.masked_key || 'Not configured in .env'}
                        </div>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        diagnosticsData?.search?.diagnostics?.providers?.serper?.available
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {diagnosticsData?.search?.diagnostics?.providers?.serper?.available ? 'Ready' : 'Offline'}
                      </span>
                    </div>

                    {/* Brave */}
                    <div className="p-3 rounded-xl bg-surface-400/50 border border-border-subtle flex items-center justify-between">
                      <div>
                        <div className="font-bold text-white flex items-center gap-1.5">
                          <span>Brave Search</span>
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-accent-cyan/20 text-accent-cyan">Secondary / Failover</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Key: {diagnosticsData?.search?.diagnostics?.providers?.brave?.masked_key || 'Not configured in .env'}
                        </div>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        diagnosticsData?.search?.diagnostics?.providers?.brave?.available
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {diagnosticsData?.search?.diagnostics?.providers?.brave?.available ? 'Ready' : 'Offline'}
                      </span>
                    </div>

                    {/* Google Custom Search */}
                    <div className="p-3 rounded-xl bg-surface-400/50 border border-border-subtle flex items-center justify-between">
                      <div>
                        <div className="font-bold text-white flex items-center gap-1.5">
                          <span>Google Custom Search</span>
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-500/20 text-slate-300">Optional Legacy</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Key: {diagnosticsData?.search?.diagnostics?.providers?.google_custom?.masked_key || 'Not configured in .env'}
                        </div>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        diagnosticsData?.search?.diagnostics?.providers?.google_custom?.available
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        {diagnosticsData?.search?.diagnostics?.providers?.google_custom?.available ? 'Ready' : 'Offline'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="text-[10px] text-slate-400 p-2 rounded bg-surface-400/30 border border-border-subtle/50">
                  <span className="font-semibold text-slate-300">Zero Credential Exposure Guarantee:</span> API keys are stored securely on the backend server and masked (<code className="text-brand-300 font-mono">***</code>) before transmission. Keys are never embedded in client HTML or generated codebases.
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
