'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { ResearchSession, ProblemOpportunity, TechStackSelection } from '@/types';
import { OpportunitiesGrid } from '@/components/OpportunitiesGrid';
import { RefinementDrawer } from '@/components/RefinementDrawer';
import { StackModal } from '@/components/StackModal';
import {
  Lightbulb,
  Sparkles,
  ArrowRight,
  Filter,
  Calendar,
  Layers,
  Compass,
  AlertCircle,
} from 'lucide-react';

export default function OpportunitiesPage() {
  const router = useRouter();

  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [opportunities, setOpportunities] = useState<ProblemOpportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals & Drawers state
  const [isRefinementOpen, setIsRefinementOpen] = useState(false);
  const [selectedOppForStack, setSelectedOppForStack] = useState<ProblemOpportunity | null>(null);
  const [isBuildingId, setIsBuildingId] = useState<string | null>(null);

  // Fetch all research sessions on mount
  useEffect(() => {
    async function loadSessions() {
      setIsLoading(true);
      try {
        const list = await api.listResearchSessions();
        setSessions(list);
        if (list && list.length > 0) {
          const firstId = list[0].id;
          setSelectedSessionId(firstId);
          await loadProblemsForSession(firstId);
        } else {
          setIsLoading(false);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load research history');
        setIsLoading(false);
      }
    }
    loadSessions();
  }, []);

  const loadProblemsForSession = async (sessionId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const opps = await api.getProblems(sessionId);
      setOpportunities(opps || []);
    } catch (err: any) {
      console.warn('Failed to fetch candidate problems:', err);
      setOpportunities([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const sId = e.target.value;
    setSelectedSessionId(sId);
    if (sId) {
      loadProblemsForSession(sId);
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

  const handleCustomStackBuild = async (stack: TechStackSelection) => {
    if (!selectedOppForStack) return;
    const opp = selectedOppForStack;
    setIsBuildingId(opp.id);
    setSelectedOppForStack(null);

    try {
      const project = await api.createProject(
        opp.title,
        opp.description || opp.summary || '',
        opp.id,
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

      router.push(`/projects/${project.id}`);
    } catch (err: any) {
      setError(`Failed to build custom project: ${err.message}`);
      setIsBuildingId(null);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 border border-brand-500/30">
              CANDIDATE DISCOVERY ARCHIVE
            </span>
            <span className="text-xs text-slate-500 font-mono">Real-World Factual Evidence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white mt-1">
            Candidate Problem Opportunities
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-300">
            Review discovered opportunities ranked by severity, career relevance, and startup potential.
            Filter across historical research sessions or pivot existing candidates.
          </p>
        </div>

        <Link
          href="/"
          className="btn-press flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-accent-purple px-4 py-2.5 text-xs font-bold text-white shadow-md hover:from-brand-500 hover:to-accent-purple/90 shrink-0"
        >
          <Sparkles className="h-4 w-4" />
          <span>New Prompt Discovery</span>
        </Link>
      </div>

      {/* Session Filter Bar */}
      {sessions.length > 0 && (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-md">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
            <Filter className="h-4 w-4 text-brand-400" />
            <span>Research Query Session:</span>
          </div>

          <div className="flex-1 max-w-xl">
            <select
              value={selectedSessionId}
              onChange={handleSessionChange}
              className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3 py-2 text-xs font-medium text-white focus:outline-none focus:border-brand-500"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.query} &bull; ({s.created_at ? new Date(s.created_at).toLocaleDateString() : 'Recent'})
                </option>
              ))}
            </select>
          </div>

          <span className="text-xs text-slate-400 font-mono shrink-0">
            {opportunities.length} candidate(s) loaded
          </span>
        </div>
      )}

      {/* Error notification */}
      {error && (
        <div className="rounded-xl border border-accent-rose/30 bg-accent-rose/10 p-4 text-xs text-accent-rose flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-64 rounded-2xl border border-border-subtle bg-surface-300/40 animate-pulse"
            />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        /* Empty State */
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-12 text-center max-w-xl mx-auto">
          <Compass className="mx-auto h-12 w-12 text-brand-400 mb-3" />
          <h2 className="text-base font-bold text-white">No Research Sessions Logged Yet</h2>
          <p className="mt-1 text-xs text-slate-400 leading-relaxed">
            Submit an industry or engineering friction in Prompt Studio to uncover real-world problems
            with community evidence.
          </p>
          <Link
            href="/"
            className="btn-press mt-5 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-brand-500/20 hover:bg-brand-500"
          >
            <span>🚀 Launch One-Prompt Studio &rarr;</span>
          </Link>
        </div>
      ) : opportunities.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-8 text-center text-xs text-slate-400">
          No candidates found for this research session.
        </div>
      ) : (
        /* Discovered Opportunities Grid */
        <OpportunitiesGrid
          opportunities={opportunities}
          onOpenRefinement={() => setIsRefinementOpen(true)}
          onCustomizeStack={(opp) => setSelectedOppForStack(opp)}
          onDirectBuild={handleDirectBuild}
          isBuildingId={isBuildingId}
        />
      )}

      {/* AI Conversational Refinement Drawer */}
      <RefinementDrawer
        isOpen={isRefinementOpen}
        onClose={() => setIsRefinementOpen(false)}
        sessionId={selectedSessionId}
        currentOpportunities={opportunities}
        onOpportunitiesUpdated={(newOpps: ProblemOpportunity[]) => {
          setOpportunities(newOpps);
        }}
      />

      {/* Tech Stack Customizer Modal */}
      {selectedOppForStack && (
        <StackModal
          isOpen={Boolean(selectedOppForStack)}
          onClose={() => setSelectedOppForStack(null)}
          opportunity={selectedOppForStack}
          onConfirmBuild={async (_opp, stack) => {
            await handleCustomStackBuild(stack);
          }}
        />
      )}
    </div>
  );
}
