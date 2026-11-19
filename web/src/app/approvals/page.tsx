'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Approval } from '@/types';
import { ShieldCheck, Check, X, Clock, AlertTriangle } from 'lucide-react';

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [filter, setFilter] = useState<'pending' | 'all'>('pending');
  const [isLoading, setIsLoading] = useState(true);
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const fetchApprovals = async () => {
    try {
      const data = await api.listApprovals(filter === 'pending' ? 'pending' : '');
      setApprovals(data);
    } catch (err) {
      console.error('Failed to load approvals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [filter]);

  const handleDecision = async (approvalId: string, decision: 'approve' | 'reject') => {
    setActionInProgress(approvalId);
    try {
      await api.respondApproval(approvalId, decision, feedback[approvalId] || '');
      await fetchApprovals();
    } catch (err) {
      console.error('Approval decision failed:', err);
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">Security & Autonomous Approvals</h1>
          <p className="mt-1 text-xs text-slate-400">
            Review and govern AI agent actions, workspace generation tasks, and deployment executions.
          </p>
        </div>

        <div className="flex rounded-xl border border-border-subtle bg-surface-300 p-1 text-xs">
          <button
            onClick={() => setFilter('pending')}
            className={`btn-press rounded-lg px-3.5 py-1.5 font-semibold transition-all ${
              filter === 'pending' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Pending Only
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`btn-press rounded-lg px-3.5 py-1.5 font-semibold transition-all ${
              filter === 'all' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            All History
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-2xl border border-border-subtle bg-surface-300/40 animate-pulse" />
          ))}
        </div>
      ) : approvals.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-12 text-center">
          <ShieldCheck className="mx-auto h-12 w-12 text-accent-emerald mb-3" />
          <h3 className="text-sm font-bold text-white">No Pending Approvals</h3>
          <p className="mt-1 text-xs text-slate-400">
            All agent actions have been resolved or are operating within permitted parameters.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((app) => (
            <div
              key={app.id}
              className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-2xl border border-border-subtle bg-surface-300/80 p-5 shadow-md"
            >
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    app.status === 'pending'
                      ? 'bg-accent-amber/20 text-accent-amber border border-accent-amber/30'
                      : app.status === 'approved'
                      ? 'bg-accent-emerald/20 text-accent-emerald'
                      : 'bg-accent-rose/20 text-accent-rose'
                  }`}>
                    {app.status}
                  </span>
                  <span className="text-xs font-bold text-brand-300 uppercase">Stage: {app.stage}</span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {app.created_at ? new Date(app.created_at).toLocaleTimeString() : ''}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white">{app.action || 'Agent Action Gate'}</h3>
                <p className="mt-1 text-xs text-slate-300">{app.description}</p>

                {app.status === 'pending' && (
                  <input
                    type="text"
                    value={feedback[app.id] || ''}
                    onChange={(e) => setFeedback({ ...feedback, [app.id]: e.target.value })}
                    placeholder="Optional feedback / directive to the agent..."
                    className="mt-3 w-full max-w-md rounded-lg border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                  />
                )}
              </div>

              {app.status === 'pending' && (
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleDecision(app.id, 'reject')}
                    disabled={actionInProgress === app.id}
                    className="btn-press flex items-center gap-1.5 rounded-xl border border-accent-rose/40 bg-accent-rose/10 px-4 py-2 text-xs font-bold text-accent-rose hover:bg-accent-rose/20 disabled:opacity-50"
                  >
                    <X className="h-3.5 w-3.5" />
                    <span>Reject</span>
                  </button>

                  <button
                    onClick={() => handleDecision(app.id, 'approve')}
                    disabled={actionInProgress === app.id}
                    className="btn-press flex items-center gap-1.5 rounded-xl bg-accent-emerald px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-emerald-600 disabled:opacity-50"
                  >
                    <Check className="h-3.5 w-3.5" />
                    <span>Approve</span>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
