'use client';

import React from 'react';
import { ProblemOpportunity } from '@/types';
import { Sparkles, MessageSquare, Sliders, ArrowRight, ShieldCheck, TrendingUp, Users, DollarSign } from 'lucide-react';

interface OpportunitiesGridProps {
  opportunities: ProblemOpportunity[];
  onOpenRefinement: () => void;
  onCustomizeStack: (opportunity: ProblemOpportunity) => void;
  onDirectBuild: (opportunity: ProblemOpportunity) => void;
  isBuildingId?: string | null;
}

export function OpportunitiesGrid({
  opportunities,
  onOpenRefinement,
  onCustomizeStack,
  onDirectBuild,
  isBuildingId,
}: OpportunitiesGridProps) {
  if (!opportunities || opportunities.length === 0) return null;

  return (
    <div className="space-y-6">
      {/* Top Banner with Refinement CTA */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-2xl border border-brand-500/30 bg-gradient-to-r from-brand-950/40 via-surface-300 to-surface-300 p-5 shadow-lg">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-accent-emerald animate-pulse" />
            <h2 className="text-base font-bold text-white">4 Validated Problem Candidates Discovered</h2>
          </div>
          <p className="mt-1 text-xs text-slate-300 max-w-2xl">
            Ranked using dynamic research across platform discussions, market pain points, and technical feasibility. Customize the stack or converse with AI to pivot.
          </p>
        </div>

        <button
          onClick={onOpenRefinement}
          className="btn-press flex items-center gap-2 rounded-xl border border-brand-400/40 bg-brand-600/20 px-4 py-2.5 text-xs font-bold text-brand-300 shadow-md hover:bg-brand-600/30"
        >
          <MessageSquare className="h-4 w-4 text-brand-400" />
          <span>💬 Converse & Refine with AI</span>
        </button>
      </div>

      {/* Grid of 4 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {opportunities.map((opp, index) => {
          const score = Math.round(opp.viability_score || opp.confidence_score || opp.overall_score || 85);
          const isCurrentBuilding = isBuildingId === opp.id;

          return (
            <div
              key={opp.id || index}
              className="group relative flex flex-col justify-between rounded-2xl border border-border-subtle bg-surface-300/80 p-6 transition-all duration-200 hover:border-brand-500/40 hover:bg-surface-200/80 shadow-md"
            >
              <div>
                {/* Header: Audience badge & score badge */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="flex items-center gap-1 rounded-md bg-surface-400 px-2.5 py-1 text-[11px] font-semibold text-slate-300 border border-border-subtle">
                    <Users className="h-3 w-3 text-slate-400" />
                    <span>{opp.target_audience || opp.target_user || 'Target Market'}</span>
                  </span>

                  <div className="flex items-center gap-1.5 rounded-full border border-accent-emerald/40 bg-accent-emerald/10 px-2.5 py-0.5 text-xs font-bold text-accent-emerald">
                    <TrendingUp className="h-3 w-3" />
                    <span>{score}% Viability</span>
                  </div>
                </div>

                {/* Title */}
                <h3 className="text-base font-bold text-white group-hover:text-brand-300 transition-colors">
                  {opp.title}
                </h3>

                {/* Description */}
                <p className="mt-2 text-xs leading-relaxed text-slate-300">
                  {opp.description || opp.summary}
                </p>

                {/* Market Gap / Commercial Note */}
                {(opp.market_gap || opp.monetization || opp.monetization_potential) && (
                  <div className="mt-3 flex items-start gap-2 rounded-xl bg-surface-400/60 p-2.5 text-[11px] text-slate-300 border border-border-subtle">
                    <DollarSign className="h-3.5 w-3.5 text-accent-emerald shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white">Market Gap: </span>
                      <span>{opp.market_gap || opp.monetization || opp.monetization_potential}</span>
                    </div>
                  </div>
                )}

                {/* Pillars Breakdown */}
                {opp.pillar_breakdown && (
                  <div className="mt-3.5 grid grid-cols-3 gap-2 text-[10px] font-mono text-slate-400 border-t border-border-subtle pt-3">
                    <div className="bg-surface-400/80 p-2 rounded-lg text-center">
                      <div className="text-slate-500 text-[9px] uppercase">Demand</div>
                      <div className="font-bold text-white text-xs mt-0.5">{opp.pillar_breakdown.pillar_a_market_demand || 85}%</div>
                    </div>
                    <div className="bg-surface-400/80 p-2 rounded-lg text-center">
                      <div className="text-slate-500 text-[9px] uppercase">Feasibility</div>
                      <div className="font-bold text-white text-xs mt-0.5">{opp.pillar_breakdown.pillar_b_technical_feasibility || 90}%</div>
                    </div>
                    <div className="bg-surface-400/80 p-2 rounded-lg text-center">
                      <div className="text-slate-500 text-[9px] uppercase">Moat</div>
                      <div className="font-bold text-white text-xs mt-0.5">{opp.pillar_breakdown.pillar_c_developer_moat || 88}%</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex items-center gap-2.5 pt-3 border-t border-border-subtle">
                <button
                  onClick={() => onCustomizeStack(opp)}
                  disabled={Boolean(isBuildingId)}
                  className="btn-press flex-1 flex items-center justify-center gap-1.5 rounded-xl border border-brand-500/40 bg-surface-400/90 py-2.5 text-xs font-semibold text-brand-300 hover:bg-brand-500/10 hover:border-brand-500 disabled:opacity-50"
                >
                  <Sliders className="h-3.5 w-3.5 text-brand-400" />
                  <span>Customize Stack ⚡</span>
                </button>

                <button
                  onClick={() => onDirectBuild(opp)}
                  disabled={Boolean(isBuildingId)}
                  className="btn-press flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-brand-600 to-accent-purple py-2.5 text-xs font-bold text-white shadow-md shadow-brand-500/20 hover:from-brand-500 hover:to-accent-purple/90 disabled:opacity-50"
                >
                  {isCurrentBuilding ? (
                    <>
                      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      <span>Generating Blueprint...</span>
                    </>
                  ) : (
                    <>
                      <span>Direct Build</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
