'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { DeploymentRecord } from '@/types';
import { CloudLightning, ExternalLink, CheckCircle2, Clock, Globe } from 'lucide-react';

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<DeploymentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDeployments() {
      try {
        const list = await api.getDeployments();
        setDeployments(list);
      } catch (err) {
        console.error('Failed to load deployments:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadDeployments();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-black text-white">Cloud Deployments & Health Checks</h1>
        <p className="mt-1 text-xs text-slate-400">
          History of all autonomous and guided production cloud builds, live endpoints, and health probes.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-28 rounded-2xl border border-border-subtle bg-surface-300/40 animate-pulse" />
          ))}
        </div>
      ) : deployments.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-12 text-center">
          <CloudLightning className="mx-auto h-12 w-12 text-slate-500 mb-3" />
          <h3 className="text-sm font-bold text-white">No Cloud Deployments Executed</h3>
          <p className="mt-1 text-xs text-slate-400">
            When you build and deploy a project, its manifests and live verification status will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {deployments.map((dep) => (
            <div
              key={dep.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-border-subtle bg-surface-300/80 p-5 shadow-md"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 uppercase">
                    Provider: {dep.provider}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Project: {dep.project_id.slice(0, 8)}
                  </span>
                </div>

                <div className="flex items-center gap-2 mt-1">
                  <Globe className="h-4 w-4 text-accent-emerald" />
                  <a
                    href={dep.deployment_url || '#'}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-mono text-brand-300 hover:underline flex items-center gap-1"
                  >
                    <span>{dep.deployment_url || 'https://problempilot-demo.vercel.app'}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {dep.health_check_result?.verified ? (
                  <span className="flex items-center gap-1.5 rounded-full border border-accent-emerald/40 bg-accent-emerald/10 px-3 py-1 text-xs font-bold text-accent-emerald">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Healthy (200 OK)</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 rounded-full border border-slate-700 bg-surface-400 px-3 py-1 text-xs font-medium text-slate-400">
                    <Clock className="h-3.5 w-3.5" />
                    <span>Manifest Ready</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
