'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { AuditLogItem } from '@/types';
import {
  ShieldAlert,
  Search,
  RefreshCw,
  Clock,
  Layers,
  CheckCircle2,
  AlertCircle,
  FileCode2,
  X,
  Filter,
} from 'lucide-react';

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeModalLog, setActiveModalLog] = useState<AuditLogItem | null>(null);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const categoryParam = selectedCategory === 'all' ? undefined : selectedCategory;
      const data = await api.listAuditLogs(categoryParam, 100);
      setLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedCategory]);

  const categories = [
    { id: 'all', label: 'All Events' },
    { id: 'auth', label: 'Auth & Profile' },
    { id: 'project', label: 'Projects' },
    { id: 'approval', label: 'Approvals' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'research', label: 'Research' },
  ];

  const filteredLogs = logs.filter((log) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      (log.action && log.action.toLowerCase().includes(term)) ||
      (log.description && log.description.toLowerCase().includes(term)) ||
      (log.category && log.category.toLowerCase().includes(term))
    );
  });

  const getCategoryBadgeClass = (category: string) => {
    switch (category) {
      case 'auth':
        return 'bg-purple-500/15 text-purple-300 border-purple-500/30';
      case 'approval':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      case 'project':
        return 'bg-brand-500/15 text-brand-300 border-brand-500/30';
      case 'integrations':
        return 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30';
      case 'research':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      default:
        return 'bg-slate-500/15 text-slate-300 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <ShieldAlert className="h-6 w-6 text-brand-400" />
            Security & System Audit Ledger
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Immutable audit trail of security state transitions, pipeline executions, approvals, and OAuth connections.
          </p>
        </div>
        <button
          onClick={fetchLogs}
          disabled={isLoading}
          className="btn-press self-start sm:self-auto inline-flex items-center gap-2 rounded-xl bg-surface-300 hover:bg-surface-200 border border-border-subtle px-4 py-2 text-xs font-semibold text-slate-200 transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* Category Pills & Search */}
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`btn-press whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold transition-all duration-150 ${
                selectedCategory === cat.id
                  ? 'bg-brand-600 text-white shadow-sm shadow-brand-500/20'
                  : 'bg-surface-300/70 text-slate-400 hover:text-slate-200 hover:bg-surface-300'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="relative min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search action or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl bg-surface-300/80 border border-border-subtle pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
        </div>
      </div>

      {/* Table of Audit Logs */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 rounded-2xl border border-border-subtle bg-surface-300/40 animate-pulse" />
          ))}
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-12 text-center">
          <ShieldAlert className="mx-auto h-12 w-12 text-slate-600 mb-3" />
          <h3 className="text-sm font-bold text-white">No Audit Events Logged</h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
            System actions, security mode changes, and pipeline operations will automatically record here.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 overflow-hidden shadow-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border-subtle bg-surface-400/50 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {filteredLogs.map((log) => {
                  const isSuccess = log.status === 'success' || !log.status;
                  return (
                    <tr
                      key={log.id}
                      className="hover:bg-surface-200/50 transition-colors duration-150"
                    >
                      <td className="py-3 px-4 text-slate-400 font-mono whitespace-nowrap">
                        {log.created_at
                          ? new Date(log.created_at).toLocaleString([], {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit',
                            })
                          : 'Recent'}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${getCategoryBadgeClass(
                            log.category
                          )}`}
                        >
                          {log.category || 'general'}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-slate-200 whitespace-nowrap">
                        {log.action}
                      </td>
                      <td className="py-3 px-4 text-slate-300 max-w-md truncate">
                        {log.description}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                            isSuccess
                              ? 'bg-accent-emerald/10 text-emerald-400 border border-accent-emerald/20'
                              : 'bg-accent-rose/10 text-rose-400 border border-accent-rose/20'
                          }`}
                        >
                          {isSuccess ? (
                            <CheckCircle2 className="h-3 w-3" />
                          ) : (
                            <AlertCircle className="h-3 w-3" />
                          )}
                          <span className="capitalize">{log.status || 'success'}</span>
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => setActiveModalLog(log)}
                          className="btn-press p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-surface-400 transition-colors"
                          title="View JSON Payload"
                        >
                          <FileCode2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* JSON Inspection Modal */}
      {activeModalLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-lg rounded-2xl border border-border-subtle bg-surface-300 p-6 shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <FileCode2 className="h-4 w-4 text-brand-400" />
                <h3 className="text-sm font-bold text-white font-mono">
                  {activeModalLog.action}
                </h3>
              </div>
              <button
                onClick={() => setActiveModalLog(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-surface-400"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                  Event Description
                </span>
                <p className="mt-0.5 text-xs text-slate-200">
                  {activeModalLog.description}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                  Payload & Details
                </span>
                <pre className="mt-1.5 max-h-64 overflow-y-auto rounded-xl bg-surface-400/90 p-3 text-[11px] font-mono text-slate-300 border border-border-subtle">
                  {JSON.stringify(
                    {
                      id: activeModalLog.id,
                      user_id: activeModalLog.user_id,
                      project_id: activeModalLog.project_id,
                      details: activeModalLog.details,
                      status: activeModalLog.status,
                      error_message: activeModalLog.error_message,
                      created_at: activeModalLog.created_at,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={() => setActiveModalLog(null)}
                className="btn-press rounded-xl bg-surface-400 px-4 py-1.5 text-xs font-semibold text-slate-200 hover:bg-surface-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
