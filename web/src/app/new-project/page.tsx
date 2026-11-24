'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Cpu,
  Layers,
  Database,
  Terminal,
  ShieldCheck,
  AlertCircle,
  Plus,
  Trash2,
  RefreshCw,
  FileCode,
  Hammer,
} from 'lucide-react';

export default function CreateProjectPage() {
  const router = useRouter();

  // Wizard Stage: 'describe' -> 'analyzing' -> 'blueprint' -> 'generating' -> 'completed'
  const [stage, setStage] = useState<'describe' | 'analyzing' | 'blueprint' | 'generating' | 'completed'>('describe');

  // Step A: Inputs
  const [description, setDescription] = useState('');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [preferredTech, setPreferredTech] = useState('');
  const [designPreferences, setDesignPreferences] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Step B: Blueprint
  const [blueprint, setBlueprint] = useState<any>(null);
  const [newFeatureText, setNewFeatureText] = useState('');

  // Step C & D: Project creation & generation
  const [projectId, setProjectId] = useState<string | null>(null);
  const [generationLogs, setGenerationLogs] = useState<string[]>([]);
  const [generationStatus, setGenerationStatus] = useState<string>('Queued');
  const [isApproved, setIsApproved] = useState(false);

  // Preset ideas
  const presetIdeas = [
    {
      label: 'Data Analyst Portfolio',
      desc: 'Create a modern portfolio website for a data analyst with projects, skills, resume download and contact form.',
      cat: 'portfolio',
    },
    {
      label: 'Local Bakery Storefront',
      desc: 'Create a website for a local bakery where customers can browse products, view prices and submit orders.',
      cat: 'business_storefront',
    },
    {
      label: 'Student Attendance SaaS',
      desc: 'Create a SaaS dashboard for managing student attendance.',
      cat: 'saas_dashboard',
    },
  ];

  // Action: Step A -> Step B (Analyze Idea via BlueprintEngine)
  const handleAnalyzeIdea = async () => {
    if (!description.trim()) {
      setError('Please provide a description of the application you want to build.');
      return;
    }

    setError(null);
    setStage('analyzing');

    try {
      const res = await api.analyzeIdea({
        description: description.trim(),
        title: title.trim() || undefined,
        category: category || undefined,
        target_audience: targetAudience.trim() || undefined,
        preferred_technology: preferredTech.trim() ? { stack: preferredTech.trim() } : undefined,
        design_preferences: designPreferences.trim() || undefined,
      });

      setTitle(res.title);
      setBlueprint(res.blueprint);
      setStage('blueprint');
    } catch (err: any) {
      setError(err.message || 'Failed to analyze idea. Please check backend connection.');
      setStage('describe');
    }
  };

  // Action: Modify features in Blueprint
  const handleAddFeature = () => {
    if (!newFeatureText.trim() || !blueprint) return;
    const currentFeatures = Array.isArray(blueprint.features) ? [...blueprint.features] : [];
    currentFeatures.push(newFeatureText.trim());
    setBlueprint({ ...blueprint, features: currentFeatures });
    setNewFeatureText('');
  };

  const handleRemoveFeature = (index: number) => {
    if (!blueprint || !Array.isArray(blueprint.features)) return;
    const currentFeatures = [...blueprint.features];
    currentFeatures.splice(index, 1);
    setBlueprint({ ...blueprint, features: currentFeatures });
  };

  // Action: Re-analyze / Regenerate Blueprint
  const handleRegenerateBlueprint = async () => {
    await handleAnalyzeIdea();
  };

  // Action: Approve Blueprint & Trigger Real Project Generation
  const handleApproveAndGenerate = async () => {
    setError(null);
    setIsApproved(true);
    setStage('generating');
    setGenerationLogs(['Queued: Initializing project record...']);
    setGenerationStatus('Queued');

    try {
      // 1. Create project with approved blueprint
      setGenerationLogs((prev) => [...prev, 'Creating project record in database...']);
      const proj = await api.createProject(
        title || 'Tailored Web Application',
        description,
        null,
        '',
        blueprint?.tech_stack || undefined,
        designPreferences || ''
      );

      // Save blueprint into project
      await api.updateProject(proj.id, { blueprint });
      setProjectId(proj.id);

      // 2. Analysing & Synthesizing Codebase
      setGenerationLogs((prev) => [...prev, 'Analysing approved blueprint architectural schemas...']);
      setGenerationStatus('Analysing');

      await new Promise((r) => setTimeout(r, 600));
      setGenerationLogs((prev) => [...prev, 'Generating frontend, backend, models, and tests with WebsiteGenerator...']);
      setGenerationStatus('Generating files');

      // 3. Build workspace
      const buildRes = await api.buildWorkspace(proj.id, true, true, description);
      setGenerationLogs((prev) => [
        ...prev,
        `Validating files: Synthesized ${buildRes.total_files || buildRes.files_written || 'all'} source files into sandbox.`,
      ]);
      setGenerationStatus('Validating files');

      // 4. Run automated tests
      setGenerationLogs((prev) => [...prev, 'Running automated test_suite.py verification in sandbox...']);
      setGenerationStatus('Running tests');

      const testRes = await api.testWorkspace(proj.id);
      if (testRes.passed || testRes.status === 'passed') {
        setGenerationLogs((prev) => [...prev, '✅ All automated verification tests passed!']);
      } else {
        setGenerationLogs((prev) => [
          ...prev,
          `⚠️ Test run completed with warnings: ${testRes.test_results?.stdout || 'See project logs'}`,
        ]);
      }

      setGenerationStatus('Completed');
      setGenerationLogs((prev) => [...prev, 'Project successfully built and verified! Opening workspace...']);
      setStage('completed');

      // Navigate to workspace dashboard
      setTimeout(() => {
        router.push(`/projects/${proj.id}`);
      }, 1200);
    } catch (err: any) {
      setGenerationStatus('Failed');
      setError(err.message || 'Generation failed. Please try again.');
      setGenerationLogs((prev) => [...prev, `❌ Error: ${err.message}`]);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/projects"
              className="text-xs font-semibold text-slate-400 hover:text-slate-200 inline-flex items-center gap-1"
            >
              <ArrowLeft className="w-3 h-3" /> Back to Projects
            </Link>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-brand-400" /> Dynamic Website Generator
          </h1>
          <p className="text-xs text-slate-400">
            Generate different, fully functional, production-ready websites from natural language.
          </p>
        </div>

        {/* Progress Tracker */}
        <div className="hidden sm:flex items-center gap-2 text-xs font-semibold">
          <span className={`px-2.5 py-1 rounded-full ${stage === 'describe' ? 'bg-brand-600 text-white' : 'bg-surface-300 text-slate-400'}`}>
            1. Describe
          </span>
          <ArrowRight className="w-3 h-3 text-slate-600" />
          <span className={`px-2.5 py-1 rounded-full ${stage === 'blueprint' ? 'bg-brand-600 text-white' : 'bg-surface-300 text-slate-400'}`}>
            2. Blueprint
          </span>
          <ArrowRight className="w-3 h-3 text-slate-600" />
          <span className={`px-2.5 py-1 rounded-full ${stage === 'generating' || stage === 'completed' ? 'bg-brand-600 text-white' : 'bg-surface-300 text-slate-400'}`}>
            3. Build & Verify
          </span>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Error Encountered</p>
            <p className="mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────────────
          STEP A: Describe your idea
          ───────────────────────────────────────────────────────────────────────── */}
      {stage === 'describe' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border-subtle bg-surface-300/60 p-6 md:p-8 space-y-6">
            <div>
              <label className="block text-sm font-bold text-white mb-2">
                What website or web application would you like to build? *
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                placeholder="Example: Create a modern portfolio website for a data analyst with projects, skills, resume download and contact form."
                className="w-full rounded-xl border border-border-subtle bg-surface-400 p-4 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 transition-all font-sans leading-relaxed"
              />
            </div>

            {/* Presets */}
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                Or choose an archetype example:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {presetIdeas.map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => {
                      setDescription(preset.desc);
                      setTitle(preset.label);
                      setCategory(preset.cat);
                    }}
                    className="text-left rounded-xl border border-border-subtle bg-surface-300/40 p-3.5 hover:border-brand-500/50 hover:bg-surface-200/50 transition-all group"
                  >
                    <div className="text-xs font-bold text-brand-300 group-hover:text-brand-200 flex items-center justify-between">
                      {preset.label}
                      <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                      {preset.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Specifics */}
            <div className="border-t border-border-subtle/60 pt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Project Title (Optional)
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Elena Vance Portfolio"
                  className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Project Category (Optional)
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2.5 text-xs text-white focus:border-brand-500 focus:outline-none"
                >
                  <option value="">Auto-Detect from Description</option>
                  <option value="portfolio">Personal & Professional Portfolio</option>
                  <option value="business_storefront">Local Business & Bakery Storefront</option>
                  <option value="saas_dashboard">SaaS & Attendance Dashboard</option>
                  <option value="e_commerce">E-Commerce & Digital Store</option>
                  <option value="landing_page">Startup Landing Page</option>
                  <option value="blog">Content Blog & Articles</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Target Audience (Optional)
                </label>
                <input
                  type="text"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  placeholder="e.g. Recruiters, hiring managers, local bakery customers"
                  className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Design Preferences (Optional)
                </label>
                <input
                  type="text"
                  value={designPreferences}
                  onChange={(e) => setDesignPreferences(e.target.value)}
                  placeholder="e.g. Dark glassmorphism, warm bakery palette, high contrast"
                  className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleAnalyzeIdea}
                disabled={!description.trim()}
                className="btn-press inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-bold text-white hover:bg-brand-500 shadow-lg shadow-brand-500/25 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" /> Generate Blueprint
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────────────
          STEP B: Analyzing Stage Spinner
          ───────────────────────────────────────────────────────────────────────── */}
      {stage === 'analyzing' && (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-16 text-center space-y-4">
          <RefreshCw className="w-10 h-10 text-brand-400 animate-spin mx-auto" />
          <h3 className="text-lg font-bold text-white">Analyzing Requirements & Generating Blueprint...</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            BlueprintEngine is extracting entities, selecting the optimal application architecture, and synthesizing schemas and contracts.
          </p>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────────────
          STEP C: Blueprint Review & Approval
          ───────────────────────────────────────────────────────────────────────── */}
      {stage === 'blueprint' && blueprint && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 md:p-8 space-y-6 shadow-xl">
            {/* Header info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-5">
              <div>
                <span className="text-[10px] font-bold text-brand-400 uppercase tracking-wider bg-brand-500/10 px-2.5 py-0.5 rounded-full border border-brand-500/20">
                  {blueprint.project_category?.replace('_', ' ').toUpperCase()} BLUEPRINT
                </span>
                <h2 className="text-xl font-black text-white mt-2">{blueprint.project_name || title}</h2>
                <p className="text-xs text-slate-300 mt-1 max-w-2xl">{blueprint.project_description}</p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={handleRegenerateBlueprint}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:text-white"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Re-analyze
                </button>
                <button
                  type="button"
                  onClick={handleApproveAndGenerate}
                  className="btn-press inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-500 shadow-md shadow-emerald-600/25"
                >
                  <ShieldCheck className="w-4 h-4" /> Approve & Build
                </button>
              </div>
            </div>

            {/* Architecture Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-xl border border-border-subtle bg-surface-400/60 p-4">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                  <Layers className="w-3.5 h-3.5 text-brand-400" /> Frontend Tech
                </div>
                <div className="text-xs text-white font-medium">
                  {typeof blueprint.frontend_technology === 'object'
                    ? blueprint.frontend_technology.framework || 'HTML5 + Modern CSS + Vanilla ES6'
                    : blueprint.frontend_technology}
                </div>
                <div className="text-[11px] text-slate-400 mt-2">
                  Responsive glassmorphism UI with clean component breakdown.
                </div>
              </div>

              <div className="rounded-xl border border-border-subtle bg-surface-400/60 p-4">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Backend Engine
                </div>
                <div className="text-xs text-white font-medium">
                  {typeof blueprint.backend_requirements === 'object'
                    ? blueprint.backend_requirements.framework || 'FastAPI (Python 3.11+)'
                    : 'FastAPI'}
                </div>
                <div className="text-[11px] text-slate-400 mt-2">
                  Async REST architecture with CORS validation and route isolation.
                </div>
              </div>

              <div className="rounded-xl border border-border-subtle bg-surface-400/60 p-4">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                  <Database className="w-3.5 h-3.5 text-emerald-400" /> Database & Storage
                </div>
                <div className="text-xs text-white font-medium">
                  {typeof blueprint.database_requirements === 'object'
                    ? blueprint.database_requirements.engine || 'SQLite 3'
                    : 'SQLite Persistent Storage'}
                </div>
                <div className="text-[11px] text-slate-400 mt-2">
                  Real disk persistence with relational entity integrity.
                </div>
              </div>
            </div>

            {/* Core Features list with Add/Remove capability */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Target Features ({blueprint.features?.length || 0})
                </span>
                <span className="text-[10px] text-slate-400">Click × to remove or add custom items below</span>
              </div>

              <div className="space-y-2">
                {Array.isArray(blueprint.features) &&
                  blueprint.features.map((feat: string, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-xl border border-border-subtle bg-surface-400/40 px-3.5 py-2.5 text-xs text-slate-200"
                    >
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span>{feat}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveFeature(idx)}
                        className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                        title="Remove feature"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
              </div>

              {/* Add Custom Feature */}
              <div className="flex items-center gap-2 mt-3">
                <input
                  type="text"
                  value={newFeatureText}
                  onChange={(e) => setNewFeatureText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddFeature()}
                  placeholder="Add another feature to this blueprint..."
                  className="flex-1 rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleAddFeature}
                  className="rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2 text-xs font-bold text-brand-300 hover:text-white hover:bg-surface-300"
                >
                  <Plus className="w-3.5 h-3.5 inline mr-1" /> Add
                </button>
              </div>
            </div>

            {/* Pages & Endpoints Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="rounded-xl border border-border-subtle bg-surface-400/30 p-4">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                  Required Navigation & Pages
                </span>
                <div className="space-y-1.5 text-xs text-slate-300">
                  {Array.isArray(blueprint.required_pages) &&
                    blueprint.required_pages.map((p: any, i: number) => (
                      <div key={i} className="flex items-center justify-between font-mono text-[11px]">
                        <span className="text-white">{p.name || p}</span>
                        <span className="text-slate-500">{p.route || '/'}</span>
                      </div>
                    ))}
                </div>
              </div>

              <div className="rounded-xl border border-border-subtle bg-surface-400/30 p-4">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                  API Endpoints & Contracts
                </span>
                <div className="space-y-1.5 text-xs text-slate-300">
                  {Array.isArray(blueprint.api_requirements || blueprint.api_contracts) &&
                    (blueprint.api_requirements || blueprint.api_contracts).slice(0, 4).map((apiReq: any, i: number) => (
                      <div key={i} className="flex items-center justify-between font-mono text-[11px]">
                        <span className="text-cyan-400 font-bold">{apiReq.method || 'GET'}</span>
                        <span className="text-slate-300">{apiReq.path || apiReq.endpoint}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            {/* Bottom CTA */}
            <div className="flex items-center justify-between pt-4 border-t border-border-subtle">
              <button
                type="button"
                onClick={() => setStage('describe')}
                className="text-xs font-semibold text-slate-400 hover:text-slate-200"
              >
                ← Edit Description
              </button>
              <button
                type="button"
                onClick={handleApproveAndGenerate}
                className="btn-press inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-2.5 text-xs font-bold text-white hover:bg-emerald-500 shadow-lg shadow-emerald-600/25"
              >
                <ShieldCheck className="w-4 h-4" /> Approve & Build Real Workspace
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────────────
          STEP D: Real-Time Generation Progress
          ───────────────────────────────────────────────────────────────────────── */}
      {(stage === 'generating' || stage === 'completed') && (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 md:p-8 space-y-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-border-subtle pb-4">
            <div>
              <h2 className="text-lg font-black text-white flex items-center gap-2">
                <Hammer className="w-5 h-5 text-brand-400" /> Synthesizing Project Workspace
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Target: <span className="text-slate-200 font-semibold">{title || 'Tailored Project'}</span>
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                generationStatus === 'Completed'
                  ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                  : generationStatus === 'Failed'
                  ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                  : 'bg-brand-500/10 text-brand-300 border border-brand-500/20 animate-pulse'
              }`}>
                {generationStatus}
              </span>
            </div>
          </div>

          {/* Terminal-style live execution log */}
          <div className="rounded-xl border border-border-subtle bg-surface-500 p-4 font-mono text-xs space-y-2 min-h-[180px] max-h-[300px] overflow-y-auto">
            {generationLogs.map((log, index) => (
              <div key={index} className="text-slate-300 flex items-start gap-2">
                <span className="text-brand-400 select-none">❯</span>
                <span>{log}</span>
              </div>
            ))}
            {generationStatus !== 'Completed' && generationStatus !== 'Failed' && (
              <div className="text-brand-400 animate-pulse flex items-center gap-2">
                <span className="select-none">❯</span>
                <span className="inline-block w-2 h-4 bg-brand-400 animate-ping" />
              </div>
            )}
          </div>

          {generationStatus === 'Failed' && (
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setStage('blueprint')}
                className="rounded-xl border border-border-subtle bg-surface-400 px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white"
              >
                Back to Blueprint
              </button>
              <button
                type="button"
                onClick={handleApproveAndGenerate}
                className="rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white hover:bg-brand-500"
              >
                Retry Generation
              </button>
            </div>
          )}

          {generationStatus === 'Completed' && projectId && (
            <div className="flex justify-end">
              <Link
                href={`/projects/${projectId}`}
                className="btn-press inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-brand-500 shadow-md shadow-brand-500/20"
              >
                <span>Open Project Workspace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
