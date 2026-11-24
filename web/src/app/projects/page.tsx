'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Project } from '@/types';
import { FolderGit2, ArrowRight, Layers, Clock, Cpu, CheckCircle, Trash2, Sparkles } from 'lucide-react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchProjects() {
      try {
        const list = await api.listProjects();
        setProjects(list);
      } catch (err) {
        console.error('Failed to load projects:', err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchProjects();
  }, []);

  const handleDeleteProject = async (e: React.MouseEvent, id: string, name: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(`Are you sure you want to permanently delete "${name}" and its workspace?`)) {
      return;
    }
    try {
      await api.deleteProject(id, true);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err: any) {
      alert(`Failed to delete project: ${err.message}`);
    }
  };

  const stages = ['discover', 'architect', 'build', 'test', 'teach', 'deploy'];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white">Synthesized Projects</h1>
          <p className="mt-1 text-xs text-slate-400">
            All active problem-to-codebase pipelines, blueprints, and workspaces.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/new-project"
            className="btn-press flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-500 shadow-md shadow-emerald-500/20"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate Website</span>
          </Link>
          <Link
            href="/"
            className="btn-press flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white hover:bg-brand-500 shadow-md shadow-brand-500/20"
          >
            <span>+ Prompt Studio</span>
          </Link>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-44 rounded-2xl border border-border-subtle bg-surface-300/40 animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-12 text-center">
          <FolderGit2 className="mx-auto h-12 w-12 text-slate-500 mb-3" />
          <h3 className="text-sm font-bold text-white">No Projects Generated Yet</h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
            Explore domain pain points in the Prompt Studio to synthesize your first production architecture.
          </p>
          <Link
            href="/"
            className="btn-press mt-4 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-xs font-semibold text-white"
          >
            <span>Launch Prompt Studio</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {projects.map((proj) => {
            const currentStageIndex = stages.indexOf(proj.current_stage || 'architect');

            return (
              <Link
                key={proj.id}
                href={`/projects/${proj.id}`}
                className="group relative flex flex-col justify-between rounded-2xl border border-border-subtle bg-surface-300/80 p-6 transition-all duration-200 hover:border-brand-500/40 hover:bg-surface-200/90 shadow-md"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="rounded-full border border-brand-500/30 bg-brand-500/10 px-2.5 py-0.5 text-[10px] font-bold text-brand-300 uppercase tracking-wider">
                      Stage: {proj.current_stage || 'architect'}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-500 font-mono">
                        {proj.created_at ? new Date(proj.created_at).toLocaleDateString() : 'Active'}
                      </span>
                      <button
                        onClick={(e) => handleDeleteProject(e, proj.id, proj.title || proj.name || 'Untitled')}
                        className="btn-press p-1.5 rounded-lg text-slate-400 hover:text-accent-rose hover:bg-accent-rose/15 transition-colors"
                        title="Delete project"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-white group-hover:text-brand-300 transition-colors">
                    {proj.title || proj.name}
                  </h3>

                  <p className="mt-2 text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {proj.description || 'Full-stack software solution synthesized from verified problem evidence.'}
                  </p>

                  {/* Tech Stack Chips & AI Copilot Indicator */}
                  <div className="mt-3 flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {proj.tech_stack?.frontend && (
                        <span className="rounded bg-surface-400/90 border border-border-subtle px-2 py-0.5 text-[10px] text-slate-300 font-mono">
                          {Array.isArray(proj.tech_stack.frontend) ? proj.tech_stack.frontend[0] : String(proj.tech_stack.frontend).split(',')[0]}
                        </span>
                      )}
                      {proj.tech_stack?.backend && (
                        <span className="rounded bg-surface-400/90 border border-border-subtle px-2 py-0.5 text-[10px] text-slate-300 font-mono">
                          {Array.isArray(proj.tech_stack.backend) ? proj.tech_stack.backend[0] : String(proj.tech_stack.backend).split(',')[0]}
                        </span>
                      )}
                    </div>
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-brand-300 bg-brand-500/15 border border-brand-500/30 rounded-md px-1.5 py-0.5">
                      <Sparkles className="h-2.5 w-2.5" />
                      <span>AI Copilot</span>
                    </span>
                  </div>

                  {/* Stage Progress Bar */}
                  <div className="mt-4 pt-3 border-t border-border-subtle">
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1.5 font-mono">
                      <span>Pipeline Progress</span>
                      <span className="font-bold text-slate-200 capitalize">{proj.current_stage || 'architect'}</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-surface-400 overflow-hidden flex">
                      {stages.map((st, idx) => (
                        <div
                          key={st}
                          className={`flex-1 ${
                            idx <= currentStageIndex ? 'bg-brand-500' : 'bg-surface-400'
                          } ${idx < currentStageIndex ? 'border-r border-surface-300' : ''}`}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-5 flex items-center justify-between pt-3 border-t border-border-subtle text-xs font-semibold text-brand-400 group-hover:text-brand-300">
                  <span>Open Blueprint & Workspace</span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
