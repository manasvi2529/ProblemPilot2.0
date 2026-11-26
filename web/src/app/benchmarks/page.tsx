'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { BenchmarkCase, BenchmarkRunRecord } from '@/types';
import {
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  FileText,
  Activity,
  Layers,
  Search,
  ExternalLink,
  Cpu,
  Lock,
} from 'lucide-react';

export default function BenchmarksPage() {
  const { user } = useAuth();
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [runs, setRuns] = useState<BenchmarkRunRecord[]>([]);
  const [activeRun, setActiveRun] = useState<BenchmarkRunRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [user]);

  async function loadData() {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const [caseList, runList] = await Promise.all([
        api.listBenchmarkCases(),
        api.listBenchmarkRuns(),
      ]);
      setCases(caseList);
      setRuns(runList);
      if (runList.length > 0) {
        const details = await api.getBenchmarkRunDetails(runList[0].id);
        setActiveRun(details);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load benchmarks data');
    } finally {
      setLoading(false);
    }
  }

  async function handleTriggerRun() {
    if (running) return;
    setRunning(true);
    setError(null);
    try {
      const payload: { case_ids?: string[]; skip_app_eval?: boolean } = {
        skip_app_eval: true,
      };
      if (selectedCaseId !== 'all') {
        payload.case_ids = [selectedCaseId];
      }
      const newRun = await api.triggerBenchmarkRun(payload);
      const detailed = await api.getBenchmarkRunDetails(newRun.id);
      setRuns((prev) => [detailed, ...prev]);
      setActiveRun(detailed);
    } catch (err: any) {
      setError(err?.message || 'Failed to execute benchmark evaluation run');
    } finally {
      setRunning(false);
    }
  }

  async function handleSelectRun(runId: string) {
    try {
      const details = await api.getBenchmarkRunDetails(runId);
      setActiveRun(details);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch run details');
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-400">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
                Quality & Safety Benchmarks
              </h1>
            </div>
            <p className="mt-2 text-sm text-slate-400">
              Deterministic evaluation across Research Grounding, Architecture Blueprints, and 4 Independent Critical Safety Gates.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All 5 Golden Cases</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>

            <button
              onClick={handleTriggerRun}
              disabled={running}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50 shadow-lg shadow-indigo-600/20"
            >
              {running ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Benchmark
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/40 border border-red-800/50 rounded-xl text-red-300 text-sm flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Overview Stats */}
        {activeRun && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl backdrop-blur-sm">
              <span className="text-xs uppercase font-semibold text-slate-400">Suite Status</span>
              <div className="mt-2 flex items-center gap-2">
                {activeRun.overall_status === 'PASSED' ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                ) : (
                  <XCircle className="w-6 h-6 text-amber-400" />
                )}
                <span className={`text-xl font-bold ${activeRun.overall_status === 'PASSED' ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {activeRun.overall_status}
                </span>
              </div>
              <span className="text-xs text-slate-500 mt-1 block">
                {activeRun.passed_all_critical_gates ? 'All 4 critical safety gates intact' : 'Critical safety violation detected'}
              </span>
            </div>

            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl backdrop-blur-sm">
              <span className="text-xs uppercase font-semibold text-slate-400">Average Quality Score</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white">{activeRun.average_score.toFixed(1)}</span>
                <span className="text-sm text-slate-500">/ 10.0</span>
              </div>
              <span className="text-xs text-slate-500 mt-1 block">Weighted Research (30%) + Blueprint (35%) + App (35%)</span>
            </div>

            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl backdrop-blur-sm">
              <span className="text-xs uppercase font-semibold text-slate-400">Cases Passed</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-emerald-400">{activeRun.passed_cases}</span>
                <span className="text-sm text-slate-500">/ {activeRun.total_cases} total</span>
              </div>
              <span className="text-xs text-slate-500 mt-1 block">{activeRun.failed_cases} failed or degraded</span>
            </div>

            <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl backdrop-blur-sm">
              <span className="text-xs uppercase font-semibold text-slate-400">SHA-256 Digest</span>
              <div className="mt-2 font-mono text-xs text-indigo-400 truncate">
                {activeRun.sha256_report_digest || 'Uncertified'}
              </div>
              <span className="text-xs text-slate-500 mt-1 block">Tamper-evident verification hash</span>
            </div>
          </div>
        )}

        {/* Main Content: Runs List & Detailed Evaluation View */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Previous Runs Sidebar */}
          <div className="space-y-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Evaluation History
            </h2>
            <div className="space-y-2">
              {runs.map((r) => (
                <button
                  key={r.id}
                  onClick={() => handleSelectRun(r.id)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    activeRun?.id === r.id
                      ? 'bg-indigo-950/40 border-indigo-500/50 text-white'
                      : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">Suite {r.suite_name}</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-mono ${
                        r.overall_status === 'PASSED'
                          ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                          : 'bg-amber-950/80 text-amber-400 border border-amber-800/60'
                      }`}
                    >
                      {r.overall_status}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                    <span>Score: {r.average_score.toFixed(1)}/10</span>
                    <span>{new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </button>
              ))}

              {runs.length === 0 && !loading && (
                <div className="p-6 bg-slate-900/30 border border-slate-800 rounded-xl text-center text-sm text-slate-500">
                  No benchmark runs recorded yet. Click &quot;Run Benchmark&quot; to begin.
                </div>
              )}
            </div>
          </div>

          {/* Active Run Evaluation Breakdown */}
          <div className="lg:col-span-2 space-y-6">
            {activeRun && activeRun.case_results && (
              <>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Benchmark Cases &amp; Critical Safety Audits
                </h2>

                <div className="space-y-4">
                  {activeRun.case_results.map((c) => (
                    <div
                      key={c.id}
                      className="p-6 bg-slate-900/50 border border-slate-800 rounded-2xl space-y-5"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                              {c.case_id}
                            </span>
                            <span className="text-xs text-slate-500">v{c.case_version}</span>
                          </div>
                          <div className="mt-2 font-mono text-xs text-slate-500 truncate max-w-md">
                            Digest: {c.case_digest}
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="text-xl font-bold text-white">{c.overall_score.toFixed(1)}</span>
                          <span className="text-xs text-slate-500 block">Overall Score</span>
                        </div>
                      </div>

                      {/* Component Sub-scores */}
                      <div className="grid grid-cols-3 gap-3 p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl text-center text-xs">
                        <div>
                          <span className="text-slate-400 block">Research</span>
                          <span className="font-bold text-slate-200 mt-1 block">{c.research_score.toFixed(1)}/10</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block">Blueprint</span>
                          <span className="font-bold text-slate-200 mt-1 block">{c.blueprint_score.toFixed(1)}/10</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block">Application</span>
                          <span className="font-bold text-slate-200 mt-1 block">{c.app_score.toFixed(1)}/10</span>
                        </div>
                      </div>

                      {/* 4 Independent Critical Safety Gates */}
                      {c.gate_summary && c.gate_summary.gates && (
                        <div className="space-y-2 border-t border-slate-800/60 pt-4">
                          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                            Critical Pass/Fail Gates
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                            {Object.entries(c.gate_summary.gates).map(([name, g]: [string, any]) => (
                              <div
                                key={name}
                                className={`p-2.5 rounded-lg border flex items-center justify-between ${
                                  g.passed
                                    ? 'bg-emerald-950/20 border-emerald-800/30 text-emerald-300'
                                    : 'bg-red-950/30 border-red-800/40 text-red-300'
                                }`}
                              >
                                <div className="flex items-center gap-2">
                                  {g.passed ? (
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                  ) : (
                                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                                  )}
                                  <span className="capitalize">{name.replace('_', ' ')}</span>
                                </div>
                                <span className="font-mono text-[10px]">{g.passed ? 'PASSED' : 'FAILED'}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
