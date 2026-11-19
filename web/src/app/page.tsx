'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { ProblemOpportunity, TechStackSelection } from '@/types';
import { OpportunitiesGrid } from '@/components/OpportunitiesGrid';
import { RefinementDrawer } from '@/components/RefinementDrawer';
import { StackModal } from '@/components/StackModal';
import { Sparkles, ArrowRight, Compass, ShieldAlert, Cpu, Terminal, CheckCircle2 } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  const [prompt, setPrompt] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchStep, setSearchStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [opportunities, setOpportunities] = useState<ProblemOpportunity[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedOpportunityForStack, setSelectedOpportunityForStack] = useState<ProblemOpportunity | null>(null);
  const [isBuildingId, setIsBuildingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const samplePrompts = [
    'Automated compliance auditor for local clinic healthcare patient records',
    'Offline-first inventory sync for rural agricultural grain storage depots',
    'Secret sprawl detection and automated rotation for multi-cloud Kubernetes clusters',
    'Independent coffee roaster green bean moisture and batch defect logging',
  ];

  const handleStartSearch = async (userPrompt?: string) => {
    const text = (userPrompt || prompt).trim();
    if (!text || isSearching) return;

    if (userPrompt) setPrompt(userPrompt);

    setIsSearching(true);
    setError(null);
    setSearchStep(1);

    const stepInterval = setInterval(() => {
      setSearchStep((prev) => (prev < 4 ? prev + 1 : prev));
    }, 1200);

    try {
      const res = await api.startPromptJourney(text);
      clearInterval(stepInterval);
      setSessionId(res.session_id);
      setOpportunities(res.opportunities || []);
      setSearchStep(5);
    } catch (err: any) {
      clearInterval(stepInterval);
      setError(err.message || 'Failed to synthesize opportunities. Please verify OpenRouter API key.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleConfirmBuild = async (
    opportunity: ProblemOpportunity,
    stack: TechStackSelection
  ) => {
    setIsBuildingId(opportunity.id);
    try {
      // 1. Create project with customized stack
      const project = await api.createProject(
        opportunity.title,
        opportunity.description || opportunity.summary || '',
        opportunity.id,
        '',
        {
          frontend: [stack.frontend],
          backend: [stack.backend],
          database: stack.database,
          architecture: stack.architecture,
          testing: ['pytest', 'jest / vitest'],
          deployment: 'Docker Container / Cloud Host',
        },
        stack.customNotes
      );

      // 2. Generate customized blueprint
      await api.generateProjectBlueprint(
        project.id,
        {
          frontend: [stack.frontend],
          backend: [stack.backend],
          database: stack.database,
          architecture: stack.architecture,
        },
        stack.customNotes
      );

      // 3. Navigate directly to project architect viewer
      router.push(`/projects/${project.id}`);
    } catch (err: any) {
      setError(`Failed to build project: ${err.message}`);
      setIsBuildingId(null);
    }
  };

  const handleDirectBuild = async (opportunity: ProblemOpportunity) => {
    setIsBuildingId(opportunity.id);
    try {
      const project = await api.createProject(
        opportunity.title,
        opportunity.description || opportunity.summary || '',
        opportunity.id
      );

      await api.generateProjectBlueprint(project.id);
      router.push(`/projects/${project.id}`);
    } catch (err: any) {
      setError(`Failed to build project: ${err.message}`);
      setIsBuildingId(null);
    }
  };

  const progressSteps = [
    'Scanning developer forums and real-world domain friction...',
    'Synthesizing recurring operational pain points...',
    'Evaluating Pillar A (Demand) & Pillar B (Technical Feasibility)...',
    'Applying Pillar C Developer Moat and formulating architectures...',
  ];

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <div className="relative text-center max-w-3xl mx-auto pt-4 pb-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-3.5 py-1 text-xs font-semibold text-brand-300 mb-4">
          <Sparkles className="h-3.5 w-3.5 text-brand-400" />
          <span>Autonomous AI Problem-to-Project Intelligence</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
          Turn Any Domain Friction Into A{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 via-accent-purple to-accent-emerald">
            Shippable Codebase
          </span>
        </h1>

        <p className="mt-4 text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Type an industry, engineering bottleneck, or domain challenge. ProblemPilot uncovers high-conviction problems, formulates system architectures, and synthesizes full-stack repositories.
        </p>

        {/* Search Bar */}
        <div className="mt-8">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleStartSearch();
            }}
            className="relative flex items-center rounded-2xl border border-border-subtle bg-surface-300/90 p-2 shadow-2xl shadow-black/80 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/20"
          >
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. AI-driven cold storage temperature anomaly detection for rural vaccine logistics..."
              disabled={isSearching}
              className="flex-1 bg-transparent px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isSearching || !prompt.trim()}
              className="btn-press flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-accent-purple px-6 py-3 text-xs font-bold text-white shadow-lg shadow-brand-500/25 hover:from-brand-500 hover:to-accent-purple/90 disabled:opacity-40"
            >
              {isSearching ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <span>Explore Problems</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Sample Prompts */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <span className="text-[11px] font-semibold text-slate-400">Try exploring:</span>
            {samplePrompts.map((p, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleStartSearch(p)}
                disabled={isSearching}
                className="btn-press rounded-full border border-border-subtle bg-surface-400/70 px-3 py-1 text-[11px] text-slate-300 hover:border-brand-500/40 hover:bg-surface-300/90 disabled:opacity-50"
              >
                {p.slice(0, 42)}...
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading Progress State */}
      {isSearching && (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/60 p-6 text-center max-w-xl mx-auto shadow-xl">
          <div className="flex justify-center mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/20 text-brand-400 border border-brand-500/30">
              <Cpu className="h-6 w-6 animate-pulse" />
            </div>
          </div>
          <h3 className="text-sm font-bold text-white">Synthesizing Real-World Opportunities</h3>
          <p className="mt-1 text-xs text-brand-300 font-mono">
            {progressSteps[searchStep - 1] || 'Finalizing opportunities...'}
          </p>
          <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-surface-400">
            <div
              className="h-full bg-gradient-to-r from-brand-500 to-accent-emerald transition-all duration-500"
              style={{ width: `${(searchStep / 4) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Presentation */}
      {error && (
        <div className="rounded-xl border border-accent-rose/30 bg-accent-rose/10 p-4 text-xs text-rose-300 max-w-xl mx-auto text-center">
          {error}
        </div>
      )}

      {/* Opportunities Section */}
      {opportunities.length > 0 && !isSearching && (
        <OpportunitiesGrid
          opportunities={opportunities}
          onOpenRefinement={() => setIsDrawerOpen(true)}
          onCustomizeStack={(opp) => setSelectedOpportunityForStack(opp)}
          onDirectBuild={handleDirectBuild}
          isBuildingId={isBuildingId}
        />
      )}

      {/* Conversational Refinement Drawer */}
      <RefinementDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        sessionId={sessionId}
        currentOpportunities={opportunities}
        onOpportunitiesUpdated={(newOpps) => setOpportunities(newOpps)}
      />

      {/* Visual Stack Customizer Modal */}
      <StackModal
        isOpen={Boolean(selectedOpportunityForStack)}
        onClose={() => setSelectedOpportunityForStack(null)}
        opportunity={selectedOpportunityForStack}
        onConfirmBuild={handleConfirmBuild}
      />
    </div>
  );
}
