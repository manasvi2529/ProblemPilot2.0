'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { IntegrationsStatus, DeploymentRecord } from '@/types';
import {
  Plug,
  Github,
  Cloud,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  Server,
  Zap,
  Globe,
  Clock,
  Layers,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export default function IntegrationsPage() {
  const [status, setStatus] = useState<IntegrationsStatus | null>(null);
  const [deployments, setDeployments] = useState<DeploymentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Verification and testing states
  const [testResult, setTestResult] = useState<{ provider: string; data: any } | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);

  // Setup wizard collapsible toggles
  const [showGhWizard, setShowGhWizard] = useState(false);
  const [showVercelWizard, setShowVercelWizard] = useState(false);
  const [copiedCallback, setCopiedCallback] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statusRes, depsRes] = await Promise.allSettled([
        api.getIntegrationsStatus(),
        api.getDeployments(),
      ]);

      if (statusRes.status === 'fulfilled') {
        setStatus(statusRes.value);
      }
      if (depsRes.status === 'fulfilled') {
        setDeployments(depsRes.value);
      }
    } catch (err) {
      console.error('Failed to load integrations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleConnectGitHub = async () => {
    try {
      const data = await api.authorizeGitHub();
      if (data && data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch (err: any) {
      alert(`GitHub OAuth failed: ${err.message}`);
    }
  };

  const handleTestGitHub = async () => {
    setTestingProvider('github');
    setTestResult(null);
    try {
      const res = await api.testGitHubConnection();
      setTestResult({ provider: 'github', data: res });
    } catch (err: any) {
      setTestResult({ provider: 'github', data: { connected: false, message: err.message } });
    } finally {
      setTestingProvider(null);
    }
  };

  const handleDisconnectGitHub = async () => {
    if (!confirm('Disconnect GitHub account and revoke access tokens?')) return;
    try {
      await api.disconnectGitHub();
      await loadData();
    } catch (err: any) {
      alert(`Disconnect failed: ${err.message}`);
    }
  };

  const handleVerifyVercel = async () => {
    setTestingProvider('vercel');
    setTestResult(null);
    try {
      const res = await api.verifyVercel();
      setTestResult({ provider: 'vercel', data: res });
    } catch (err: any) {
      setTestResult({ provider: 'vercel', data: { valid: false, message: err.message } });
    } finally {
      setTestingProvider(null);
    }
  };

  const handleVerifyRender = async () => {
    setTestingProvider('render');
    setTestResult(null);
    try {
      const res = await api.verifyRender();
      setTestResult({ provider: 'render', data: res });
    } catch (err: any) {
      setTestResult({ provider: 'render', data: { valid: false, message: err.message } });
    } finally {
      setTestingProvider(null);
    }
  };

  const copyCallbackUrl = () => {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000';
    const cb = status?.callback_url || `${origin}/api/integrations/github/callback`;
    navigator.clipboard.writeText(cb);
    setCopiedCallback(true);
    setTimeout(() => setCopiedCallback(false), 2000);
  };

  const callbackUrl =
    status?.callback_url ||
    (typeof window !== 'undefined'
      ? `${window.location.origin}/api/integrations/github/callback`
      : 'http://127.0.0.1:8000/api/integrations/github/callback');

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 border border-brand-500/30">
              DEPLOYMENT & PROTOCOLS
            </span>
            <span className="text-xs text-slate-500 font-mono">Secure Token Encryption at Rest</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white mt-1">
            Cloud & GitHub Integrations Center
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-300">
            Secure OAuth 2.0 authorization, AES-256 token encryption, automated private repository
            publishing, and live cloud hosting verifications.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="btn-press flex items-center gap-1.5 rounded-xl border border-border-subtle bg-surface-300 px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white shrink-0"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Status</span>
        </button>
      </div>

      {/* Grid of Key Provider Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* AI Engine */}
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5">
          <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase">
            <span>AI Model Engine</span>
            <Zap className="h-4 w-4 text-brand-400" />
          </div>
          <div className="mt-2 text-lg font-black text-white flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${status?.ai?.configured ? 'bg-accent-emerald' : 'bg-amber-400'}`} />
            <span>{status?.ai?.configured ? 'Connected' : 'Autonomous Engine'}</span>
          </div>
          <div className="mt-1 text-xs text-slate-400 font-mono">
            Primary: {status?.ai?.provider || 'openrouter'} ({status?.ai?.model || 'default'})
          </div>
          <div className="mt-2.5 flex flex-wrap gap-1.5 text-[10px]">
            <span className={`px-2 py-0.5 rounded font-mono border ${status?.ai?.google_studio_configured ? 'border-accent-emerald/40 bg-accent-emerald/10 text-emerald-300' : 'border-slate-700 bg-slate-800/60 text-slate-400'}`}>
              Google Gemini: {status?.ai?.google_studio_configured ? '✓ Ready' : 'Key not set'}
            </span>
            <span className={`px-2 py-0.5 rounded font-mono border ${status?.ai?.openrouter_configured ? 'border-accent-emerald/40 bg-accent-emerald/10 text-emerald-300' : 'border-slate-700 bg-slate-800/60 text-slate-400'}`}>
              OpenRouter: {status?.ai?.openrouter_configured ? '✓ Ready' : 'Key not set'}
            </span>
          </div>
        </div>

        {/* GitHub Integration */}
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5">
          <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase">
            <span>GitHub OAuth 2.0</span>
            <Github className="h-4 w-4 text-white" />
          </div>
          <div className="mt-2 text-lg font-black text-white flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${status?.github?.connected ? 'bg-accent-emerald' : status?.github?.oauth_enabled ? 'bg-accent-cyan' : 'bg-slate-500'}`} />
            <span className="truncate">
              {status?.github?.connected
                ? `@${status.github.username}`
                : status?.github?.oauth_enabled
                ? 'OAuth Ready'
                : 'Setup Required'}
            </span>
          </div>
          <div className="mt-1 text-xs text-slate-400 truncate">
            {status?.github?.connected
              ? `Linked: ${status.github.connected_at ? new Date(status.github.connected_at).toLocaleDateString() : 'Active'}`
              : 'Private repo publishing & git push'}
          </div>
        </div>

        {/* Vercel Cloud */}
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5">
          <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase">
            <span>Vercel Serverless</span>
            <Cloud className="h-4 w-4 text-accent-cyan" />
          </div>
          <div className="mt-2 text-lg font-black text-white flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${status?.cloud?.vercel?.status === 'connected' ? 'bg-accent-emerald' : 'bg-accent-purple'}`} />
            <span>{status?.cloud?.vercel?.status === 'connected' ? 'API Connected' : 'Manifests Active'}</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {status?.cloud?.vercel?.expected_cost || 'Edge CDN ($0/mo)'}
          </div>
        </div>

        {/* Render Cloud */}
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5">
          <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase">
            <span>Render Cloud</span>
            <Server className="h-4 w-4 text-accent-purple" />
          </div>
          <div className="mt-2 text-lg font-black text-white flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${status?.cloud?.render?.status === 'connected' ? 'bg-accent-emerald' : 'bg-accent-purple'}`} />
            <span>{status?.cloud?.render?.status === 'connected' ? 'API Connected' : 'Manifests Active'}</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {status?.cloud?.render?.expected_cost || 'Containers ($0/mo)'}
          </div>
        </div>
      </div>

      {/* Verification Feedback Banner */}
      {testResult && (
        <div className="rounded-2xl border border-border-subtle bg-surface-300 p-4 shadow-lg flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            {testResult.data.connected || testResult.data.valid ? (
              <CheckCircle2 className="h-5 w-5 text-accent-emerald shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="h-5 w-5 text-accent-rose shrink-0 mt-0.5" />
            )}
            <div>
              <div className="text-xs font-bold text-white uppercase tracking-wider">
                {testResult.provider} Verification Result
              </div>
              <div className="text-xs text-slate-300 mt-1">
                {testResult.data.message ||
                  (testResult.data.connected
                    ? `Connected as @${testResult.data.username}. Repos: ${testResult.data.public_repos || 0}.`
                    : 'Credentials verification unconfirmed.')}
              </div>
            </div>
          </div>
          <button
            onClick={() => setTestResult(null)}
            className="text-slate-400 hover:text-white text-sm"
          >
            &times;
          </button>
        </div>
      )}

      {/* GitHub Integration Card & OAuth Details */}
      <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Github className="h-5 w-5 text-white" />
              <h2 className="text-lg font-black text-white">GitHub OAuth 2.0 Integration</h2>
              <span
                className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                  status?.github?.connected
                    ? 'bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30'
                    : status?.github?.oauth_enabled
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'bg-amber-400/20 text-amber-300 border border-amber-400/30'
                }`}
              >
                {status?.github?.connected
                  ? 'Connected'
                  : status?.github?.oauth_enabled
                  ? 'OAuth Configured'
                  : 'Configuration Needed'}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Authenticate via OAuth 2.0 with HMAC CSRF protection. Tokens are stored encrypted at rest
              using AES-256 and never exposed in frontend payloads.
            </p>
          </div>

          <button
            onClick={() => setShowGhWizard(!showGhWizard)}
            className="btn-press flex items-center gap-1.5 rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:text-white shrink-0"
          >
            <span>Setup Wizard</span>
            {showGhWizard ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>

        {status?.github?.connected ? (
          <div className="rounded-xl border border-accent-emerald/30 bg-accent-emerald/10 p-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-accent-emerald flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Authenticated Account: @{status.github.username}</span>
                </div>
                <div className="text-[11px] text-slate-300 mt-1 font-mono">
                  Granted scopes: repo (private repository generation & commit push), read:user
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleTestGitHub}
                  disabled={testingProvider === 'github'}
                  className="btn-press rounded-lg border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs font-semibold text-white hover:bg-surface-500 disabled:opacity-50"
                >
                  {testingProvider === 'github' ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  onClick={handleDisconnectGitHub}
                  className="btn-press rounded-lg border border-accent-rose/30 bg-accent-rose/10 px-3 py-1.5 text-xs font-semibold text-accent-rose hover:bg-accent-rose/20"
                >
                  Disconnect
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-border-subtle bg-surface-400/80 p-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-white">No GitHub Account Linked</div>
                <div className="text-xs text-slate-400 mt-0.5">
                  {status?.github?.oauth_enabled
                    ? 'OAuth client configured. Ready to authorize.'
                    : 'Configure GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend .env to connect.'}
                </div>
              </div>

              <button
                onClick={handleConnectGitHub}
                disabled={!status?.github?.oauth_enabled}
                className="btn-press flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-xs font-bold text-slate-950 hover:bg-slate-200 disabled:opacity-50 transition-colors shadow-md"
              >
                <Github className="h-4 w-4" />
                <span>Connect GitHub Account</span>
              </button>
            </div>
          </div>
        )}

        {/* Collapsible GitHub Setup Wizard */}
        {showGhWizard && (
          <div className="mt-4 rounded-xl border border-brand-500/30 bg-[#070b14] p-5 space-y-4">
            <h4 className="text-xs font-bold text-brand-300 uppercase tracking-wider">
              GitHub OAuth 2.0 App Setup Instructions
            </h4>
            <ol className="list-decimal list-inside space-y-2 text-xs text-slate-300">
              <li>
                Sign in to GitHub and navigate to{' '}
                <strong className="text-white">Settings &rarr; Developer Settings &rarr; OAuth Apps</strong>.
              </li>
              <li>Click <strong className="text-white">New OAuth App</strong>.</li>
              <li>
                Set <span className="font-mono text-brand-300">Application Name</span> to{' '}
                <code>ProblemPilot AI</code>.
              </li>
              <li>
                Set <span className="font-mono text-brand-300">Authorization Callback URL (Exact)</span>:
                <div className="flex items-center gap-2 mt-1.5 max-w-lg">
                  <input
                    type="text"
                    readOnly
                    value={callbackUrl}
                    className="flex-1 rounded-lg border border-border-subtle bg-black/60 px-3 py-1 text-xs font-mono text-brand-200"
                  />
                  <button
                    onClick={copyCallbackUrl}
                    className="btn-press flex items-center gap-1 rounded-lg border border-border-subtle bg-surface-400 px-2.5 py-1 text-xs font-medium text-white hover:bg-surface-500"
                  >
                    {copiedCallback ? <Check className="h-3 w-3 text-accent-emerald" /> : <Copy className="h-3 w-3" />}
                    <span>{copiedCallback ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
              </li>
              <li>
                Click <strong className="text-white">Register application</strong>, copy your{' '}
                <strong>Client ID</strong>, generate a <strong>Client Secret</strong>, and update your{' '}
                <code>.env</code> file.
              </li>
            </ol>
          </div>
        )}
      </div>

      {/* Vercel & Render Cloud Verifiers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Vercel Card */}
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cloud className="h-5 w-5 text-accent-cyan" />
              <h3 className="text-base font-bold text-white">Vercel Serverless Hosting</h3>
            </div>
            <button
              onClick={handleVerifyVercel}
              disabled={testingProvider === 'vercel'}
              className="btn-press rounded-lg border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs font-semibold text-white hover:bg-surface-500 disabled:opacity-50"
            >
              {testingProvider === 'vercel' ? 'Verifying...' : 'Verify Token'}
            </button>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Deploys full-stack Next.js and FastAPI backends automatically to global Edge CDN with custom
            domains and preview URLs.
          </p>

          <button
            onClick={() => setShowVercelWizard(!showVercelWizard)}
            className="text-xs text-brand-400 hover:text-brand-300 font-semibold flex items-center gap-1"
          >
            <span>{showVercelWizard ? 'Hide Guide' : '📘 View Vercel Token Setup Guide'}</span>
          </button>

          {showVercelWizard && (
            <div className="rounded-xl border border-border-subtle bg-[#070b14] p-4 text-xs text-slate-300 space-y-2">
              <p>1. Open <a href="https://vercel.com/account/tokens" target="_blank" rel="noreferrer" className="text-brand-300 underline">vercel.com/account/tokens</a>.</p>
              <p>2. Create a token named <code>ProblemPilot Deployer</code>.</p>
              <p>3. Add to your <code>.env</code>: <code>VERCEL_TOKEN=your_token_here</code>.</p>
            </div>
          )}
        </div>

        {/* Render Card */}
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-accent-purple" />
              <h3 className="text-base font-bold text-white">Render Container Cloud</h3>
            </div>
            <button
              onClick={handleVerifyRender}
              disabled={testingProvider === 'render'}
              className="btn-press rounded-lg border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs font-semibold text-white hover:bg-surface-500 disabled:opacity-50"
            >
              {testingProvider === 'render' ? 'Verifying...' : 'Verify Token'}
            </button>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Provides automated container deployment manifests (<code>render.yaml</code>, Dockerfiles)
            for long-running async background workers and Python microservices.
          </p>
        </div>
      </div>

      {/* Deployment Audit Trail */}
      <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white">Cloud Deployment History</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Audit log of all autonomous and guided production builds and health probes.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {deployments.length} total deployment(s)
          </span>
        </div>

        {deployments.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-400">
            No cloud deployments logged yet. Deploy a project from the Projects tab to see records here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border-subtle text-slate-400">
                  <th className="pb-3 px-3">Provider</th>
                  <th className="pb-3 px-3">Project ID</th>
                  <th className="pb-3 px-3">Status</th>
                  <th className="pb-3 px-3">Live Endpoint</th>
                  <th className="pb-3 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/50 font-mono">
                {deployments.map((dep) => (
                  <tr key={dep.id} className="hover:bg-surface-400/50">
                    <td className="py-3 px-3">
                      <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 uppercase">
                        {dep.provider}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-300">{dep.project_id.slice(0, 8)}</td>
                    <td className="py-3 px-3">
                      {dep.health_check_result?.verified ? (
                        <span className="text-accent-emerald flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>200 OK</span>
                        </span>
                      ) : (
                        <span className="text-slate-400 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{dep.status || 'Active'}</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <a
                        href={dep.deployment_url || '#'}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-300 hover:underline flex items-center gap-1"
                      >
                        <span className="truncate max-w-[200px]">
                          {dep.deployment_url || 'https://problempilot-demo.vercel.app'}
                        </span>
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-sans">
                      {dep.created_at ? new Date(dep.created_at).toLocaleDateString() : 'Recent'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
