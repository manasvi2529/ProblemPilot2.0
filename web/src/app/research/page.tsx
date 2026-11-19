'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ResearchSession, ProblemOpportunity } from '@/types';
import {
  Compass,
  ExternalLink,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Globe,
  Sparkles,
  Layers,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';

export default function ResearchPage() {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);
  const [sessionDetails, setSessionDetails] = useState<Record<string, any>>({});
  const [loadingDetailId, setLoadingDetailId] = useState<string | null>(null);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const list = await api.listResearchSessions();
      setSessions(list);
    } catch (err) {
      console.error('Failed to load research:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

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
      } catch (err) {
        console.error('Failed to load session details:', err);
      } finally {
        setLoadingDetailId(null);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2.5">
            <Compass className="h-6 w-6 text-brand-400" />
            Live Research & Evidence Explorer
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Audit trail of community discussions, Reddit/HN developer complaints, and factual evidence sources.
          </p>
        </div>
        <button
          onClick={loadSessions}
          disabled={isLoading}
          className="btn-press self-start sm:self-auto inline-flex items-center gap-2 rounded-xl bg-surface-300 hover:bg-surface-200 border border-border-subtle px-4 py-2 text-xs font-semibold text-slate-200 transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Research</span>
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-2xl border border-border-subtle bg-surface-300/40 animate-pulse" />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-12 text-center">
          <Compass className="mx-auto h-12 w-12 text-slate-500 mb-3" />
          <h3 className="text-sm font-bold text-white">No Research Sessions Logged</h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
            Launch a prompt journey on the Prompt Studio to execute web search pipelines and populate evidence.
          </p>
          <Link
            href="/"
            className="btn-press mt-4 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-brand-500/20"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Launch Prompt Studio</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((sess) => {
            const isExpanded = expandedSessionId === sess.id;
            const details = sessionDetails[sess.id];
            const isLoadingDetails = loadingDetailId === sess.id;

            return (
              <div
                key={sess.id}
                className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 shadow-md transition-all duration-200 hover:border-border-default"
              >
                <div
                  onClick={() => toggleExpandSession(sess.id)}
                  className="flex items-start justify-between cursor-pointer select-none"
                >
                  <div className="space-y-1.5 pr-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="rounded-full bg-brand-500/15 border border-brand-500/30 px-2.5 py-0.5 text-[10px] font-bold text-brand-300 uppercase tracking-wider">
                        Topic / Query
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        {sess.created_at ? new Date(sess.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-white">
                      {sess.query}
                    </h3>
                  </div>

                  <button className="btn-press p-2 rounded-xl bg-surface-400/80 text-slate-300 hover:text-white">
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 pt-3 border-t border-border-subtle">
                  <div className="rounded-xl bg-surface-400/50 p-3 border border-border-subtle">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Problems Discovered</span>
                    <div className="text-sm font-bold text-white mt-0.5">
                      {sess.problems?.length || (details?.problems?.length ?? 'Evidence Analyzed')}
                    </div>
                  </div>
                  <div className="rounded-xl bg-surface-400/50 p-3 border border-border-subtle">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Platforms Consulted</span>
                    <div className="text-xs font-semibold text-accent-cyan mt-0.5 truncate">
                      {sess.platforms ? sess.platforms.join(', ') : 'Reddit, HackerNews, StackOverflow, Dev.to'}
                    </div>
                  </div>
                </div>

                {/* Expanded Session Sources and Problem Details */}
                {isExpanded && (
                  <div className="mt-5 pt-4 border-t border-border-subtle space-y-5 animate-fade-in">
                    {isLoadingDetails ? (
                      <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
                        Retrieving evidence sources and verified problem items...
                      </div>
                    ) : (
                      <>
                        {/* Problems Section */}
                        {details?.problems && details.problems.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                              Candidate Problems Synthesized
                            </h4>
                            <div className="grid grid-cols-1 gap-3">
                              {details.problems.map((prob: ProblemOpportunity, pIdx: number) => (
                                <div
                                  key={prob.id || pIdx}
                                  className="rounded-xl bg-surface-400/70 p-4 border border-border-subtle flex flex-col justify-between"
                                >
                                  <div>
                                    <div className="flex items-center justify-between gap-2 mb-1.5">
                                      <h5 className="text-sm font-bold text-white">
                                        {prob.title}
                                      </h5>
                                      {prob.overall_score && (
                                        <span className="rounded bg-brand-500/20 border border-brand-500/30 px-2 py-0.5 text-[10px] font-bold text-brand-300">
                                          Score: {prob.overall_score}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-xs text-slate-300 leading-relaxed">
                                      {prob.description || prob.summary}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Evidence Sources Section */}
                        {details?.sources && details.sources.length > 0 && (
                          <div className="space-y-2.5">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                              Evidence Citations & Sources ({details.sources.length})
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                              {details.sources.map((src: any, sIdx: number) => (
                                <a
                                  key={src.id || sIdx}
                                  href={src.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="group flex flex-col justify-between rounded-xl bg-surface-400/40 p-3 border border-border-subtle hover:border-brand-500/40 hover:bg-surface-400/70 transition-all text-left"
                                >
                                  <div>
                                    <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                                      <span className="font-semibold text-brand-400 uppercase">
                                        {src.platform || 'Web Source'}
                                      </span>
                                      <ExternalLink className="h-3 w-3 text-slate-500 group-hover:text-brand-300 transition-colors" />
                                    </div>
                                    <h6 className="text-xs font-bold text-slate-200 line-clamp-1 group-hover:text-brand-300 transition-colors">
                                      {src.title || src.url}
                                    </h6>
                                    {src.snippet && (
                                      <p className="mt-1 text-[11px] text-slate-400 line-clamp-2">
                                        &ldquo;{src.snippet}&rdquo;
                                      </p>
                                    )}
                                  </div>
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
  );
}
