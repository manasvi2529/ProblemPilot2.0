'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Project, ChatMessage } from '@/types';
import {
  ArrowLeft,
  Layers,
  Cpu,
  Database,
  Terminal,
  Code2,
  Hammer,
  ShieldCheck,
  GraduationCap,
  CloudUpload,
  CheckCircle2,
  FileCode,
  FileText,
  AlertCircle,
  Trash2,
  Sparkles,
  Send,
  Bot,
  User as UserIcon,
  RefreshCw,
  Wand2,
  Check,
  Sliders,
  ChevronRight,
  ExternalLink,
  FlaskConical,
  Play,
  XCircle,
  Square,
  RotateCw,
  Monitor,
  Tablet,
  Smartphone,
  Maximize2,
  Bug,
  Wrench,
  Undo2,
  Activity,
  Eye,
} from 'lucide-react';

export default function ProjectDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [blueprint, setBlueprint] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'preview' | 'copilot' | 'blueprint' | 'files' | 'test' | 'terminal' | 'teaching'>('preview');

  // Preview & Live Sandbox State
  const [previewStatus, setPreviewStatus] = useState<'not_started' | 'starting' | 'running' | 'failed' | 'stopped'>('not_started');
  const [previewPort, setPreviewPort] = useState<number | null>(null);
  const [previewPid, setPreviewPid] = useState<number | null>(null);
  const [previewUptime, setPreviewUptime] = useState<number>(0);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLogs, setPreviewLogs] = useState<string[]>([]);
  const [previewViewport, setPreviewViewport] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [previewKey, setPreviewKey] = useState(0);
  const [isStartingPreview, setIsStartingPreview] = useState(false);
  const [liveTestResults, setLiveTestResults] = useState<{
    passed: boolean;
    checks: Array<{ name: string; passed: boolean; detail: string }>;
    total_checks: number;
    passed_checks: number;
  } | null>(null);
  const [liveTesting, setLiveTesting] = useState(false);

  // AI-Assisted Debugger State
  const [aiDiagnosis, setAiDiagnosis] = useState<{
    summary: string;
    root_cause: string;
    file: string;
    original_snippet: string;
    replacement_snippet: string;
    explanation_of_fix: string;
  } | null>(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [applyingFix, setApplyingFix] = useState(false);
  const [fixMessage, setFixMessage] = useState<string | null>(null);

  // Test and Verification State
  const [testResults, setTestResults] = useState<{
    status?: string;
    passed?: boolean;
    tests_passed?: number;
    tests_failed?: number;
    stdout?: string;
    stderr?: string;
    returncode?: number;
    executed_at?: string;
  } | null>(null);

  // Blueprint Re-architect State
  const [rearchitectPrompt, setRearchitectPrompt] = useState('');
  const [rearchitecting, setRearchitecting] = useState(false);

  // AI Copilot & Chat State
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [pendingTechStack, setPendingTechStack] = useState<Record<string, any> | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Iterative Modification & Snapshot State
  const [pendingChangePlan, setPendingChangePlan] = useState<any>(null);
  const [changeHistory, setChangeHistory] = useState<any[]>([]);
  const [isApplyingChange, setIsApplyingChange] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [changeSuccessMessage, setChangeSuccessMessage] = useState<string | null>(null);

  // Teaching State
  const [teachTopic, setTeachTopic] = useState('System Architecture & Trade-offs');
  const [teachLevel, setTeachLevel] = useState('interview_prep');
  const [teachLoading, setTeachLoading] = useState(false);
  const [teachExplanation, setTeachExplanation] = useState<any>(null);

  const stages = [
    { key: 'discover', label: '1. Discover' },
    { key: 'architect', label: '2. Architect' },
    { key: 'build', label: '3. Build' },
    { key: 'test', label: '4. Test' },
    { key: 'teach', label: '5. Teach' },
    { key: 'deploy', label: '6. Deploy' },
  ];

  const loadData = async () => {
    try {
      const p = await api.getProject(projectId);
      setProject(p);
      if (p.blueprint) {
        setBlueprint(p.blueprint);
      }
      loadChangeHistory();
      if (chatMessages.length === 0) {
        // Initialize welcoming Copilot message
        setChatMessages([
          {
            id: 'init-msg',
            role: 'assistant',
            content: `👋 Hi! I am your **AI Workspace Architect & Copilot** for **${p.title || p.name}**.\n\nI can help you build this project dynamically from scratch:\n- ⚡ **Synthesize the entire codebase via AI** (no preuploaded templates)\n- 🛠️ **Formulate & tailor your tech stack** (Next.js, FastAPI, PostgreSQL, Redis)\n- 📐 **Generate or update database schemas & API contracts**\n- 🧪 **Write automated test cases and deployment scripts**\n\nWhat would you like to build or modify first?`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            suggestedActions: [
              '⚡ AI Generate Entire Codebase',
              '🛠️ Re-architect Tech Stack',
              '📋 Add REST API Contracts',
              '🔒 Add Auth & JWT Verification',
            ],
          },
        ]);
      }
    } catch (err: any) {
      console.error('Failed to load project:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadPreviewStatus = async () => {
    try {
      const st = await api.getProjectPreviewStatus(projectId);
      setPreviewStatus(st.status);
      setPreviewPort(st.port);
      setPreviewPid(st.pid);
      if (st.uptime_seconds) setPreviewUptime(st.uptime_seconds);
      if (st.error_message) setPreviewError(st.error_message);

      const logData = await api.getProjectPreviewLogs(projectId, 100);
      setPreviewLogs(logData.logs || []);
      return st;
    } catch (e) {
      // Ignored if unauthenticated or network error
    }
  };

  useEffect(() => {
    loadData();
    loadPreviewStatus();
  }, [projectId]);

  useEffect(() => {
    if (previewStatus !== 'running' && previewStatus !== 'starting') return;
    const interval = setInterval(async () => {
      await loadPreviewStatus();
    }, 4000);
    return () => clearInterval(interval);
  }, [previewStatus, projectId]);

  const handleStartServer = async () => {
    setIsStartingPreview(true);
    setPreviewError(null);
    try {
      const res = await api.startProjectPreview(projectId);
      if (res.success) {
        setPreviewStatus('running');
        setPreviewPort(res.port);
        setPreviewPid(res.pid);
        setPreviewKey((k) => k + 1);
        setActiveTab('preview');
        await loadPreviewStatus();
      } else {
        setPreviewStatus('failed');
        setPreviewError(res.error || 'Server startup failed.');
        await loadPreviewStatus();
      }
    } catch (err: any) {
      setPreviewStatus('failed');
      setPreviewError(err.message || 'Failed to communicate with preview engine.');
    } finally {
      setIsStartingPreview(false);
    }
  };

  const handleStopServer = async () => {
    try {
      await api.stopProjectPreview(projectId);
      setPreviewStatus('stopped');
      await loadPreviewStatus();
    } catch (err: any) {
      alert(`Stop failed: ${err.message}`);
    }
  };

  const handleRestartServer = async () => {
    setIsStartingPreview(true);
    setPreviewError(null);
    try {
      const res = await api.restartProjectPreview(projectId);
      if (res.success) {
        setPreviewStatus('running');
        setPreviewPort(res.port);
        setPreviewKey((k) => k + 1);
        await loadPreviewStatus();
      } else {
        setPreviewStatus('failed');
        setPreviewError(res.error || 'Restart failed.');
      }
    } catch (err: any) {
      setPreviewStatus('failed');
      setPreviewError(err.message);
    } finally {
      setIsStartingPreview(false);
    }
  };

  const handleRunLiveTest = async () => {
    setLiveTesting(true);
    try {
      const res = await api.testProjectLive(projectId);
      setLiveTestResults(res);
      await loadPreviewStatus();
    } catch (err: any) {
      alert(`Live test failed: ${err.message}`);
    } finally {
      setLiveTesting(false);
    }
  };

  const handleDiagnoseError = async () => {
    setDiagnosing(true);
    setFixMessage(null);
    try {
      const res = await api.diagnoseProjectError(projectId);
      setAiDiagnosis(res);
    } catch (err: any) {
      alert(`AI Diagnosis failed: ${err.message}`);
    } finally {
      setDiagnosing(false);
    }
  };

  const handleApplyFix = async () => {
    if (!aiDiagnosis) return;
    setApplyingFix(true);
    try {
      const res = await api.applyProjectFix(
        projectId,
        aiDiagnosis.file,
        aiDiagnosis.original_snippet,
        aiDiagnosis.replacement_snippet
      );
      if (res.success) {
        setFixMessage('Targeted fix applied! Restarting sandbox...');
        setAiDiagnosis(null);
        await handleRestartServer();
      } else {
        alert(`Fix could not be applied: ${res.message}`);
      }
    } catch (err: any) {
      alert(`Failed to apply fix: ${err.message}`);
    } finally {
      setApplyingFix(false);
    }
  };

  const handleRollbackFix = async () => {
    if (!aiDiagnosis) return;
    try {
      const res = await api.rollbackProjectFix(projectId, aiDiagnosis.file);
      if (res.success) {
        alert(res.message);
        await handleRestartServer();
      } else {
        alert(`Rollback failed: ${res.message}`);
      }
    } catch (err: any) {
      alert(`Rollback failed: ${err.message}`);
    }
  };

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages, chatLoading]);

  const handleBuildWorkspace = async (useAi = true, customNotes?: string) => {
    setActionLoading('build');
    setActionResult(null);
    try {
      const res: any = await api.buildWorkspace(projectId, true, useAi, customNotes);
      if (res.approval_required) {
        setActionResult(
          `⚠️ Workspace build requires approval in ${res.mode || 'guided/hybrid'} mode. Switch to Autonomous mode in the sidebar or approve under 'Security Approvals' to proceed.`
        );
      } else {
        const genType = res.ai_generated ? 'AI synthesized from scratch' : 'generated';
        setActionResult(
          `Workspace successfully ${genType}! ${res.files_written || res.files?.length || 0} source files created.`
        );
        setActiveTab('files');
      }
      await loadData();
    } catch (err: any) {
      setActionResult(`Build failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSendMessage = async (msgText?: string) => {
    const textToSend = msgText || chatInput;
    if (!textToSend.trim() || chatLoading) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setChatMessages((prev) => [...prev, userMsg]);
    if (!msgText) setChatInput('');
    setChatLoading(true);

    try {
      const history = chatMessages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await api.chatWithProjectCopilot(projectId, textToSend.trim(), history);

      if (res.suggested_tech_stack) {
        setPendingTechStack(res.suggested_tech_stack);
      }
      if (res.change_plan) {
        setPendingChangePlan(res.change_plan);
      }

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggestedActions: res.suggested_actions,
        suggestedTechStack: res.suggested_tech_stack,
      };

      setChatMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          id: `bot-err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Sorry, I encountered an error: ${err.message}. Please check that your AI provider is configured in backend settings.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleApplyTechStack = async (stackToApply?: Record<string, any>) => {
    const targetStack = stackToApply || pendingTechStack;
    if (!targetStack) return;

    setActionLoading('stack');
    try {
      await api.applyProjectTechStack(projectId, targetStack);
      setPendingTechStack(null);
      setActionResult('Tech stack updated and applied to project successfully!');
      await loadData();
    } catch (err: any) {
      alert(`Failed to apply tech stack: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSuggestTechStack = async () => {
    setActionLoading('suggest-stack');
    try {
      const res = await api.suggestProjectTechStack(projectId, 'Modern, production full-stack', false);
      if (res.tech_stack) {
        setPendingTechStack(res.tech_stack);
        const botMsg: ChatMessage = {
          id: `bot-stack-${Date.now()}`,
          role: 'assistant',
          content: `### 🔮 AI Synthesized Tech Stack Recommendation\n\nI have formulated an optimal, domain-tailored tech stack for **${project?.name}**:\n\n- **Frontend**: ${Array.isArray(res.tech_stack.frontend) ? res.tech_stack.frontend.join(', ') : res.tech_stack.frontend}\n- **Backend**: ${Array.isArray(res.tech_stack.backend) ? res.tech_stack.backend.join(', ') : res.tech_stack.backend}\n- **Database**: ${res.tech_stack.database}\n- **Architecture**: ${res.tech_stack.architecture}\n\n*${res.tech_stack.rationale || ''}*\n\nClick **Apply This Tech Stack** below to lock it in and re-generate your blueprint.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          suggestedTechStack: res.tech_stack,
        };
        setChatMessages((prev) => [...prev, botMsg]);
      }
    } catch (err: any) {
      alert(`Could not synthesize tech stack: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const loadChangeHistory = async () => {
    try {
      const res = await api.getProjectChangeHistory(projectId);
      setChangeHistory(res.history || []);
    } catch {
      // ignore
    }
  };

  const handleApproveChangePlan = async () => {
    if (!pendingChangePlan) return;
    setIsApplyingChange(true);
    setChangeSuccessMessage(null);
    try {
      const res = await api.applyProjectChange(projectId, pendingChangePlan.plan_id, true, pendingChangePlan);
      if (res.success) {
        setChangeSuccessMessage(res.message || 'Changes applied successfully!');
        setPreviewKey((k) => k + 1);
        await loadData();
        await loadChangeHistory();
        await loadPreviewStatus();
        setChatMessages((prev) => [
          ...prev,
          {
            id: `bot-applied-${Date.now()}`,
            role: 'assistant',
            content: `✅ **Changes Approved & Applied:**\n- **Version**: \`v${res.version}\` created\n- **Modified Files**: ${res.files_modified?.join(', ') || 'None'}\n- **New Files**: ${res.files_created?.join(', ') || 'None'}\n- **Live Preview**: ${res.preview_reloaded ? '🔄 Refreshed with new code' : 'Standby'}\n\nYour application was updated non-destructively.`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
        setPendingChangePlan(null);
      } else {
        alert(res.error || 'Failed to apply changes');
      }
    } catch (err: any) {
      alert(`Error applying changes: ${err.message}`);
    } finally {
      setIsApplyingChange(false);
    }
  };

  const handleRejectChangePlan = async () => {
    if (!pendingChangePlan) return;
    try {
      await api.applyProjectChange(projectId, pendingChangePlan.plan_id, false);
      setChatMessages((prev) => [
        ...prev,
        {
          id: `bot-rejected-${Date.now()}`,
          role: 'assistant',
          content: `❌ **Change Plan Rejected.** No modifications were applied to your project files. You can provide additional instructions or ask for a different approach.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setPendingChangePlan(null);
    } catch {
      setPendingChangePlan(null);
    }
  };

  const handleRollbackVersion = async (version?: number) => {
    setIsRollingBack(true);
    try {
      const res = await api.rollbackProjectChange(projectId, version);
      if (res.success) {
        setChangeSuccessMessage(`Successfully rolled back to version ${res.version}`);
        setPreviewKey((k) => k + 1);
        await loadData();
        await loadChangeHistory();
        await loadPreviewStatus();
        setChatMessages((prev) => [
          ...prev,
          {
            id: `bot-rb-${Date.now()}`,
            role: 'assistant',
            content: `⏪ **Project Rolled Back:** Workspace restored to snapshot \`v${res.version}\`. Running preview refreshed.`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } else {
        alert(res.error || 'Rollback failed');
      }
    } catch (err: any) {
      alert(`Rollback error: ${err.message}`);
    } finally {
      setIsRollingBack(false);
    }
  };

  const handleDownloadZip = async () => {
    setActionLoading('download');
    try {
      const blob = await api.downloadProjectZip(projectId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${(project?.name || 'project').toLowerCase().replace(/[^a-z0-9_]/g, '_')}_codebase.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setActionResult('Project codebase zip downloaded successfully!');
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteProject = async () => {
    if (
      !confirm(
        `Are you sure you want to permanently delete "${
          project?.title || project?.name || 'this project'
        }" and all its workspace files?`
      )
    ) {
      return;
    }
    setActionLoading('delete');
    try {
      await api.deleteProject(projectId, true);
      router.push('/projects');
    } catch (err: any) {
      alert(`Failed to delete project: ${err.message}`);
      setActionLoading(null);
    }
  };

  const handleTestWorkspace = async () => {
    setActionLoading('test');
    setActionResult(null);
    try {
      const res = await api.testWorkspace(projectId);
      if (res.test_results) {
        setTestResults({
          ...res.test_results,
          passed: res.passed ?? res.test_results.passed,
          tests_passed: res.tests_passed,
          tests_failed: res.tests_failed,
        });
      } else {
        setTestResults({
          status: res.status,
          passed: res.passed,
          tests_passed: res.tests_passed,
          tests_failed: res.tests_failed,
        });
      }
      setActiveTab('test');
      setActionResult(
        `Verification complete: ${res.passed ? '✓ All Automated Tests Passed' : '⚠️ Test run completed with warnings'}. ${res.tests_passed || 0} passed, ${res.tests_failed || 0} failed.`
      );
      await loadData();
    } catch (err: any) {
      setActionResult(`Test check: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRearchitect = async (customInstructions?: string, presetStack?: Record<string, any>) => {
    setRearchitecting(true);
    setActionResult(null);
    try {
      const stack = presetStack || project?.tech_stack || {
        frontend: ['Next.js 14', 'Tailwind CSS'],
        backend: ['FastAPI', 'Python 3.11'],
        database: 'PostgreSQL Async',
        architecture: 'Modular Monolith / REST API',
      };
      const res = await api.applyProjectTechStack(projectId, stack, true, customInstructions || rearchitectPrompt);
      if (res.blueprint) {
        setBlueprint(res.blueprint);
      }
      setActionResult('✨ Architecture Blueprint successfully re-architected with AI!');
      setRearchitectPrompt('');
      await loadData();
    } catch (err: any) {
      setActionResult(`Re-architecting failed: ${err.message}`);
    } finally {
      setRearchitecting(false);
    }
  };

  const handleStepClick = async (stepKey: string) => {
    if (stepKey === 'discover') {
      router.push('/discover');
    } else if (stepKey === 'architect') {
      setActiveTab('blueprint');
    } else if (stepKey === 'build') {
      setActiveTab('files');
    } else if (stepKey === 'test') {
      setActiveTab('test');
      if (!testResults) {
        await handleTestWorkspace();
      }
    } else if (stepKey === 'teach') {
      setActiveTab('teaching');
    } else if (stepKey === 'deploy') {
      await handleDeploy();
    }
  };

  const handleDeploy = async () => {
    setActionLoading('deploy');
    setActionResult(null);
    try {
      const res = await api.deployCloud(projectId, 'vercel');
      setActionResult(
        `Cloud deployment manifest generated. URL: ${res.deployment_url || 'https://problempilot-demo.vercel.app'}`
      );
      await loadData();
    } catch (err: any) {
      setActionResult(`Deploy status: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleAskTeacher = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!teachTopic.trim()) return;
    setTeachLoading(true);
    try {
      const res = await api.teachConcept(projectId, teachTopic.trim(), teachLevel);
      setTeachExplanation(res.explanation);
    } catch (err: any) {
      setActionResult(`Teacher error: ${err.message}`);
    } finally {
      setTeachLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-surface-300 animate-pulse rounded-lg" />
        <div className="h-64 bg-surface-300 animate-pulse rounded-2xl" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-accent-rose mb-3" />
        <h2 className="text-base font-bold text-white">Project Not Found</h2>
        <Link href="/projects" className="btn-press mt-4 inline-block text-xs text-brand-400">
          &larr; Return to Projects
        </Link>
      </div>
    );
  }

  const currentStageIndex = stages.findIndex((s) => s.key === project.current_stage);

  return (
    <div className="space-y-8">
      {/* Back and Title Header */}
      <div>
        <Link
          href="/projects"
          className="btn-press inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white mb-3"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Projects</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 border border-brand-500/30">
                {project.repository_name || 'AI Software Architecture'}
              </span>
              <span className="text-xs text-slate-500">ID: {project.id.slice(0, 8)}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white mt-1">
              {project.title || project.name}
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-slate-300 max-w-3xl">
              {project.description}
            </p>
          </div>

          {/* Action Trigger Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => {
                setActiveTab('preview');
                if (previewStatus !== 'running') {
                  handleStartServer();
                }
              }}
              disabled={isStartingPreview}
              className="btn-press flex items-center gap-1.5 rounded-xl border border-emerald-500/60 bg-gradient-to-r from-emerald-600/40 to-teal-500/30 px-3.5 py-2 text-xs font-bold text-emerald-200 hover:from-emerald-600/60 hover:to-teal-500/40 disabled:opacity-50 shadow-md"
              title="Launch and preview live running website"
            >
              <Play className="h-3.5 w-3.5 text-accent-emerald" />
              <span>
                {previewStatus === 'running'
                  ? `👁 View Website (: ${previewPort})`
                  : isStartingPreview
                  ? 'Booting Sandbox...'
                  : '▶ Preview Website'}
              </span>
            </button>

            <button
              onClick={() => handleBuildWorkspace(true)}
              disabled={Boolean(actionLoading)}
              className="btn-press flex items-center gap-1.5 rounded-xl border border-brand-500/50 bg-gradient-to-r from-brand-600/30 to-brand-500/20 px-3.5 py-2 text-xs font-bold text-brand-300 hover:from-brand-600/40 hover:to-brand-500/30 disabled:opacity-50 shadow-sm"
              title="Generate full codebase with AI from scratch"
            >
              <Sparkles className="h-3.5 w-3.5 text-brand-400 animate-pulse" />
              <span>{actionLoading === 'build' ? 'AI Synthesizing Files...' : '⚡ AI Build Workspace'}</span>
            </button>

            <button
              onClick={handleTestWorkspace}
              disabled={Boolean(actionLoading)}
              className="btn-press flex items-center gap-1.5 rounded-xl border border-accent-emerald/40 bg-accent-emerald/20 px-3.5 py-2 text-xs font-bold text-accent-emerald hover:bg-accent-emerald/30 disabled:opacity-50"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>{actionLoading === 'test' ? 'Testing...' : 'Test Suite'}</span>
            </button>

            <button
              onClick={handleDeploy}
              disabled={Boolean(actionLoading)}
              className="btn-press flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-brand-600 to-accent-purple px-4 py-2 text-xs font-bold text-white shadow-md hover:from-brand-500 hover:to-accent-purple/90 disabled:opacity-50"
            >
              <CloudUpload className="h-3.5 w-3.5" />
              <span>{actionLoading === 'deploy' ? 'Deploying...' : 'Deploy'}</span>
            </button>

            <button
              onClick={handleDownloadZip}
              disabled={Boolean(actionLoading)}
              className="btn-press flex items-center gap-1.5 rounded-xl border border-cyan-500/40 bg-cyan-500/20 px-3.5 py-2 text-xs font-bold text-cyan-300 hover:bg-cyan-500/30 disabled:opacity-50"
              title="Download full project codebase as zip"
            >
              <FileCode className="h-3.5 w-3.5" />
              <span>{actionLoading === 'download' ? 'Zipping...' : 'Download Zip'}</span>
            </button>

            <button
              onClick={handleDeleteProject}
              disabled={Boolean(actionLoading)}
              className="btn-press flex items-center gap-1.5 rounded-xl border border-accent-rose/30 bg-accent-rose/10 px-3 py-2 text-xs font-bold text-accent-rose hover:bg-accent-rose/20 disabled:opacity-50"
              title="Delete project workspace"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>{actionLoading === 'delete' ? 'Deleting...' : 'Delete'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Action Notification Alert */}
      {actionResult && (
        <div className="rounded-xl border border-brand-500/40 bg-brand-500/10 p-3.5 text-xs text-brand-200 flex items-center justify-between">
          <span>{actionResult}</span>
          <button onClick={() => setActionResult(null)} className="text-slate-400 hover:text-white text-sm">
            &times;
          </button>
        </div>
      )}

      {/* Interactive Pipeline Stage Stepper */}
      <div className="rounded-2xl border border-border-subtle bg-surface-300/60 p-4 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">
              Pipeline Lifecycle
            </span>
            <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-mono font-bold text-brand-300 border border-brand-500/30">
              ACTIVE STAGE: {project.current_stage ? project.current_stage.toUpperCase() : 'ARCHITECT'}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            Click any stage to navigate or execute action &rarr;
          </span>
        </div>

        <div className="flex items-center justify-between overflow-x-auto pb-1 gap-1">
          {stages.map((st, i) => {
            const isCompleted = i < currentStageIndex;
            const isCurrent = i === currentStageIndex;

            return (
              <React.Fragment key={st.key}>
                <button
                  type="button"
                  onClick={() => handleStepClick(st.key)}
                  title={`Navigate to ${st.label}`}
                  className={`btn-press group flex items-center gap-2 shrink-0 px-3 py-1.5 rounded-xl border transition-all duration-200 ${
                    isCurrent
                      ? 'bg-brand-600/30 border-brand-500/60 shadow-lg shadow-brand-500/10'
                      : isCompleted
                      ? 'bg-surface-400/40 border-accent-emerald/30 hover:bg-accent-emerald/10'
                      : 'bg-surface-400/20 border-transparent hover:bg-surface-400/60 hover:border-border-subtle'
                  }`}
                >
                  <div
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold transition-all ${
                      isCompleted
                        ? 'bg-accent-emerald text-white'
                        : isCurrent
                        ? 'bg-brand-600 text-white ring-4 ring-brand-500/30 shadow-md animate-pulse'
                        : 'bg-surface-400 text-slate-400 group-hover:text-slate-200'
                    }`}
                  >
                    {isCompleted ? '✓' : i + 1}
                  </div>
                  <span
                    className={`text-xs transition-colors ${
                      isCurrent
                        ? 'text-white font-bold'
                        : isCompleted
                        ? 'text-slate-200 font-semibold group-hover:text-white'
                        : 'text-slate-400 font-medium group-hover:text-slate-200'
                    }`}
                  >
                    {st.label}
                  </span>
                </button>
                {i < stages.length - 1 && (
                  <span className="text-slate-600 shrink-0 font-mono text-xs px-1">&rarr;</span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Configured Tech Stack Summary Banner */}
      <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-brand-400" />
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Project Tech Stack & Architecture
            </span>
          </div>
          <button
            onClick={handleSuggestTechStack}
            disabled={actionLoading === 'suggest-stack'}
            className="btn-press flex items-center gap-1.5 rounded-lg border border-brand-500/30 bg-brand-500/10 px-2.5 py-1 text-[11px] font-semibold text-brand-300 hover:bg-brand-500/20"
          >
            <Sparkles className="h-3 w-3 text-brand-400" />
            <span>{actionLoading === 'suggest-stack' ? 'Synthesizing...' : 'Re-synthesize with AI'}</span>
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-xl border border-border-subtle bg-surface-400/60 p-3">
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Frontend</span>
            <div className="text-xs font-bold text-white mt-1">
              {project.tech_stack && Array.isArray(project.tech_stack.frontend)
                ? project.tech_stack.frontend.join(', ')
                : project.tech_stack?.frontend || 'HTML5 Glassmorphic UI'}
            </div>
          </div>
          <div className="rounded-xl border border-border-subtle bg-surface-400/60 p-3">
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Backend</span>
            <div className="text-xs font-bold text-white mt-1">
              {project.tech_stack && Array.isArray(project.tech_stack.backend)
                ? project.tech_stack.backend.join(', ')
                : project.tech_stack?.backend || 'FastAPI Async Framework'}
            </div>
          </div>
          <div className="rounded-xl border border-border-subtle bg-surface-400/60 p-3">
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Database</span>
            <div className="text-xs font-bold text-white mt-1">
              {project.tech_stack?.database || 'SQLite (Dev) / PostgreSQL Async'}
            </div>
          </div>
          <div className="rounded-xl border border-border-subtle bg-surface-400/60 p-3">
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Architecture</span>
            <div className="text-xs font-bold text-white mt-1">
              {project.tech_stack?.architecture || 'Modular Monolith / REST API'}
            </div>
          </div>
        </div>

        {/* Pending Tech Stack Apply Banner if suggested */}
        {pendingTechStack && (
          <div className="mt-3 rounded-xl border border-accent-cyan/30 bg-accent-cyan/10 p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in">
            <div className="text-xs text-accent-cyan space-y-0.5">
              <span className="font-bold block">✨ New AI Tech Stack Ready to Apply:</span>
              <span className="text-slate-300">
                {Array.isArray(pendingTechStack.frontend)
                  ? pendingTechStack.frontend.join(', ')
                  : pendingTechStack.frontend}{' '}
                &bull;{' '}
                {Array.isArray(pendingTechStack.backend)
                  ? pendingTechStack.backend.join(', ')
                  : pendingTechStack.backend}{' '}
                &bull; {pendingTechStack.database}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => handleApplyTechStack(pendingTechStack)}
                disabled={actionLoading === 'stack'}
                className="btn-press flex items-center gap-1.5 rounded-lg bg-accent-cyan px-3 py-1.5 text-xs font-bold text-slate-900 hover:bg-cyan-300 shadow-sm"
              >
                <Check className="h-3.5 w-3.5" />
                <span>Apply & Save</span>
              </button>
              <button
                onClick={() => setPendingTechStack(null)}
                className="btn-press rounded-lg border border-border-subtle bg-surface-400 px-2.5 py-1.5 text-xs text-slate-400 hover:text-white"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border-subtle overflow-x-auto">
        <button
          onClick={() => setActiveTab('preview')}
          className={`btn-press flex items-center gap-2 border-b-2 px-5 py-3 text-xs font-bold transition-colors shrink-0 ${
            activeTab === 'preview'
              ? 'border-brand-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Play className="h-4 w-4 text-accent-emerald" />
          <span>Live Website Preview</span>
          <span
            className={`rounded-full px-1.5 py-0.2 text-[9px] font-bold ${
              previewStatus === 'running'
                ? 'bg-accent-emerald/20 text-emerald-300'
                : previewStatus === 'starting'
                ? 'bg-amber-400/20 text-amber-300'
                : previewStatus === 'failed'
                ? 'bg-accent-rose/20 text-rose-300'
                : 'bg-surface-400 text-slate-400'
            }`}
          >
            {previewStatus === 'running' ? `Running :${previewPort}` : previewStatus}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('files')}
          className={`btn-press flex items-center gap-2 border-b-2 px-5 py-3 text-xs font-bold transition-colors shrink-0 ${
            activeTab === 'files'
              ? 'border-brand-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCode className="h-4 w-4" />
          <span>Workspace Files ({project.files?.length || 0})</span>
        </button>
        <button
          onClick={() => setActiveTab('terminal')}
          className={`btn-press flex items-center gap-2 border-b-2 px-5 py-3 text-xs font-bold transition-colors shrink-0 ${
            activeTab === 'terminal'
              ? 'border-brand-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Terminal className="h-4 w-4 text-cyan-400" />
          <span>Terminal Logs</span>
          {previewLogs.length > 0 && (
            <span className="rounded-full bg-surface-400 px-1.5 py-0.2 text-[9px] font-mono text-slate-300">
              {previewLogs.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('test')}
          className={`btn-press flex items-center gap-2 border-b-2 px-5 py-3 text-xs font-bold transition-colors shrink-0 ${
            activeTab === 'test'
              ? 'border-brand-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FlaskConical className="h-4 w-4 text-accent-emerald" />
          <span>Test & Verification</span>
          {testResults && (
            <span
              className={`rounded-full px-1.5 py-0.2 text-[9px] font-bold ${
                testResults.passed
                  ? 'bg-accent-emerald/20 text-emerald-300'
                  : 'bg-accent-rose/20 text-rose-300'
              }`}
            >
              {testResults.passed ? 'Passing' : 'Failing'}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('copilot')}
          className={`btn-press flex items-center gap-2 border-b-2 px-5 py-3 text-xs font-bold transition-colors shrink-0 ${
            activeTab === 'copilot'
              ? 'border-brand-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="h-4 w-4 text-brand-400" />
          <span>AI Copilot</span>
        </button>
        <button
          onClick={() => setActiveTab('blueprint')}
          className={`btn-press flex items-center gap-2 border-b-2 px-5 py-3 text-xs font-bold transition-colors shrink-0 ${
            activeTab === 'blueprint'
              ? 'border-brand-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Blueprint</span>
        </button>
        <button
          onClick={() => setActiveTab('teaching')}
          className={`btn-press flex items-center gap-2 border-b-2 px-5 py-3 text-xs font-bold transition-colors shrink-0 ${
            activeTab === 'teaching'
              ? 'border-brand-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <GraduationCap className="h-4 w-4" />
          <span>AI Teacher</span>
        </button>
      </div>

      {/* Tab: Live Website Preview */}
      {activeTab === 'preview' && (
        <div className="space-y-4">
          {/* Preview Control Toolbar */}
          <div className="rounded-2xl border border-border-subtle bg-surface-300/90 p-4 shadow-xl">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Left: Status badge and URL */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-2.5 w-2.5 rounded-full ${
                      previewStatus === 'running'
                        ? 'bg-accent-emerald animate-ping'
                        : previewStatus === 'starting'
                        ? 'bg-amber-400 animate-pulse'
                        : previewStatus === 'failed'
                        ? 'bg-accent-rose'
                        : 'bg-slate-500'
                    }`}
                  />
                  <span className="text-xs font-bold uppercase tracking-wider text-white">
                    {previewStatus === 'running'
                      ? `Running (Port ${previewPort})`
                      : previewStatus === 'starting'
                      ? 'Starting Sandbox...'
                      : previewStatus === 'failed'
                      ? 'Failed'
                      : previewStatus === 'stopped'
                      ? 'Stopped'
                      : 'Not Started'}
                  </span>
                </div>

                {previewStatus === 'running' && (
                  <div className="flex items-center gap-2 rounded-xl bg-surface-400/80 px-3 py-1 border border-border-subtle font-mono text-[11px] text-brand-300">
                    <span className="text-slate-400">URL:</span>
                    <span>http://localhost:{previewPort}</span>
                    <a
                      href={`http://localhost:${previewPort}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-400 hover:text-white ml-1"
                      title="Open in new browser tab"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </div>
                )}

                {previewStatus === 'running' && previewUptime > 0 && (
                  <span className="text-[11px] text-slate-400 font-mono">
                    uptime: {Math.floor(previewUptime / 60)}m {previewUptime % 60}s
                  </span>
                )}
              </div>

              {/* Center: Viewport Switcher */}
              <div className="flex items-center gap-1 bg-surface-400/60 p-1 rounded-xl border border-border-subtle self-start lg:self-center">
                <button
                  type="button"
                  onClick={() => setPreviewViewport('desktop')}
                  className={`btn-press flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium ${
                    previewViewport === 'desktop'
                      ? 'bg-brand-600 text-white font-bold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="Desktop View (100%)"
                >
                  <Monitor className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Desktop</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewViewport('tablet')}
                  className={`btn-press flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium ${
                    previewViewport === 'tablet'
                      ? 'bg-brand-600 text-white font-bold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="Tablet View (768px)"
                >
                  <Tablet className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Tablet</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewViewport('mobile')}
                  className={`btn-press flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium ${
                    previewViewport === 'mobile'
                      ? 'bg-brand-600 text-white font-bold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="Mobile View (375px)"
                >
                  <Smartphone className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Mobile</span>
                </button>
              </div>

              {/* Right: Action Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                {previewStatus !== 'running' ? (
                  <button
                    onClick={handleStartServer}
                    disabled={isStartingPreview}
                    className="btn-press flex items-center gap-1.5 rounded-xl bg-accent-emerald px-3.5 py-1.5 text-xs font-bold text-slate-900 hover:bg-emerald-400 shadow-sm disabled:opacity-50"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>{isStartingPreview ? 'Booting...' : 'Start Server'}</span>
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleRestartServer}
                      disabled={isStartingPreview}
                      className="btn-press flex items-center gap-1.5 rounded-xl border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-surface-500"
                      title="Restart sandbox process"
                    >
                      <RotateCw className={`h-3.5 w-3.5 ${isStartingPreview ? 'animate-spin' : ''}`} />
                      <span>Restart</span>
                    </button>
                    <button
                      onClick={handleStopServer}
                      className="btn-press flex items-center gap-1.5 rounded-xl border border-accent-rose/30 bg-accent-rose/10 px-3 py-1.5 text-xs font-medium text-accent-rose hover:bg-accent-rose/20"
                      title="Stop server"
                    >
                      <Square className="h-3.5 w-3.5" />
                      <span>Stop</span>
                    </button>
                    <button
                      onClick={() => setPreviewKey((k) => k + 1)}
                      className="btn-press flex items-center gap-1.5 rounded-xl border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-surface-500"
                      title="Refresh iframe frame"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      <span>Refresh</span>
                    </button>
                  </>
                )}

                <button
                  onClick={handleRunLiveTest}
                  disabled={liveTesting}
                  className="btn-press flex items-center gap-1.5 rounded-xl border border-brand-500/40 bg-brand-500/20 px-3 py-1.5 text-xs font-bold text-brand-300 hover:bg-brand-500/30 disabled:opacity-50"
                  title="Run automated interactive verification tests against live server"
                >
                  <ShieldCheck className="h-3.5 w-3.5 text-brand-400" />
                  <span>{liveTesting ? 'Testing...' : 'Live E2E Test'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Live Test Results Alert (if run) */}
          {liveTestResults && (
            <div
              className={`rounded-2xl border p-4 shadow-lg ${
                liveTestResults.passed
                  ? 'border-accent-emerald/40 bg-accent-emerald/10'
                  : 'border-accent-rose/40 bg-accent-rose/10'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className={`h-4 w-4 ${liveTestResults.passed ? 'text-accent-emerald' : 'text-accent-rose'}`} />
                  <span className="text-xs font-bold text-white">
                    Live Interactive Verification Results: {liveTestResults.passed_checks} / {liveTestResults.total_checks} Checks Passed
                  </span>
                </div>
                <button onClick={() => setLiveTestResults(null)} className="text-slate-400 hover:text-white text-xs">
                  &times; Dismiss
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {liveTestResults.checks.map((c, i) => (
                  <div key={i} className="rounded-xl bg-surface-400/80 p-2.5 border border-border-subtle text-xs flex items-start gap-2">
                    <span className={`font-bold ${c.passed ? 'text-accent-emerald' : 'text-accent-rose'}`}>
                      {c.passed ? '✓' : '✗'}
                    </span>
                    <div>
                      <div className="font-semibold text-white">{c.name}</div>
                      <div className="text-[11px] text-slate-400">{c.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error & AI Diagnosis Card (if failed) */}
          {previewStatus === 'failed' && (
            <div className="rounded-2xl border border-accent-rose/40 bg-accent-rose/10 p-5 space-y-4 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-accent-rose shrink-0" />
                  <div>
                    <h4 className="text-xs font-bold text-white">Application Startup or Runtime Error</h4>
                    <p className="text-[11px] text-rose-200 mt-0.5">{previewError || 'Process terminated with non-zero exit code.'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleDiagnoseError}
                    disabled={diagnosing}
                    className="btn-press flex items-center gap-1.5 rounded-xl bg-brand-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-brand-500 shadow-sm"
                  >
                    <Bug className="h-3.5 w-3.5 text-amber-300" />
                    <span>{diagnosing ? 'AI Diagnosing Error...' : 'Ask AI to Diagnose & Fix'}</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('terminal')}
                    className="btn-press rounded-xl border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs text-slate-300 hover:text-white"
                  >
                    View Logs
                  </button>
                </div>
              </div>

              {/* AI Diagnosis Details & Proposed Targeted Fix */}
              {aiDiagnosis && (
                <div className="rounded-xl border border-brand-500/40 bg-surface-400/90 p-4 space-y-3 mt-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-brand-400" />
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      AI Diagnosis & Targeted Code Fix
                    </span>
                  </div>
                  <div>
                    <div className="text-xs font-bold text-accent-cyan">{aiDiagnosis.summary}</div>
                    <p className="text-xs text-slate-300 mt-1">{aiDiagnosis.root_cause}</p>
                    <div className="text-[11px] text-brand-300 font-mono mt-1">Target File: {aiDiagnosis.file}</div>
                  </div>

                  {aiDiagnosis.original_snippet && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-semibold text-rose-400 uppercase">Original Failing Code:</span>
                      <pre className="rounded bg-black/60 p-2 font-mono text-[11px] text-rose-300 overflow-x-auto">
                        <code>{aiDiagnosis.original_snippet}</code>
                      </pre>
                    </div>
                  )}

                  {aiDiagnosis.replacement_snippet && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-semibold text-emerald-400 uppercase">Targeted Replacement:</span>
                      <pre className="rounded bg-black/60 p-2 font-mono text-[11px] text-emerald-300 overflow-x-auto">
                        <code>{aiDiagnosis.replacement_snippet}</code>
                      </pre>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-2">
                    <button
                      onClick={handleApplyFix}
                      disabled={applyingFix}
                      className="btn-press flex items-center gap-1.5 rounded-lg bg-accent-emerald px-3.5 py-1.5 text-xs font-bold text-slate-900 hover:bg-emerald-400 shadow-sm"
                    >
                      <Wrench className="h-3.5 w-3.5" />
                      <span>{applyingFix ? 'Applying Fix...' : 'Approve & Apply Fix'}</span>
                    </button>
                    <button
                      onClick={handleRollbackFix}
                      className="btn-press flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-400 px-3 py-1.5 text-xs text-slate-300 hover:text-white"
                      title="Rollback previous fix from backup"
                    >
                      <Undo2 className="h-3.5 w-3.5" />
                      <span>Rollback</span>
                    </button>
                  </div>
                </div>
              )}

              {fixMessage && (
                <div className="rounded-lg bg-emerald-500/20 border border-emerald-500/30 p-2.5 text-xs text-emerald-300 font-medium">
                  {fixMessage}
                </div>
              )}
            </div>
          )}

          {/* Interactive Frame Viewer */}
          <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-3 flex justify-center items-center overflow-hidden min-h-[640px]">
            {previewStatus === 'running' ? (
              <div
                className={`transition-all duration-300 w-full h-[640px] rounded-xl overflow-hidden border border-border-subtle bg-black shadow-2xl ${
                  previewViewport === 'tablet'
                    ? 'max-w-[768px]'
                    : previewViewport === 'mobile'
                    ? 'max-w-[375px]'
                    : 'w-full'
                }`}
              >
                <iframe
                  key={previewKey}
                  src={`/api/preview/${projectId}/proxy/`}
                  title="Live Generated Website Preview"
                  className="w-full h-full border-0 bg-white"
                  sandbox="allow-scripts allow-forms allow-same-origin allow-downloads"
                />
              </div>
            ) : previewStatus === 'starting' ? (
              <div className="text-center py-24 space-y-4">
                <div className="mx-auto h-12 w-12 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
                <h3 className="text-sm font-bold text-white">Booting Isolated Sandbox Container...</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Allocating dynamic TCP port, configuring sanitized execution environment, and verifying liveness health check probe.
                </p>
              </div>
            ) : (
              <div className="text-center py-20 space-y-4 max-w-md mx-auto">
                <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-brand-600/30 to-accent-emerald/20 border border-emerald-500/30 mx-auto flex items-center justify-center text-accent-emerald shadow-lg">
                  <Play className="h-8 w-8 ml-1 fill-current" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Interactive Website Sandbox Ready</h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Launch this generated project in a sandboxed runtime to preview the real frontend and interact with live backend APIs.
                  </p>
                </div>
                <button
                  onClick={handleStartServer}
                  disabled={isStartingPreview}
                  className="btn-press inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-accent-emerald to-teal-500 px-5 py-2.5 text-xs font-bold text-slate-900 hover:from-emerald-400 hover:to-teal-400 shadow-md shadow-emerald-500/20"
                >
                  <Play className="h-4 w-4 fill-current" />
                  <span>{isStartingPreview ? 'Booting Server...' : 'Launch Live Website Preview'}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Terminal Logs */}
      {activeTab === 'terminal' && (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-3">
            <div className="flex items-center gap-2 font-mono text-xs text-slate-300">
              <Terminal className="h-4 w-4 text-cyan-400" />
              <span className="font-bold text-white">SANDBOX PROCESS TERMINAL</span>
              {previewPid && <span className="text-slate-500">(PID: {previewPid})</span>}
              {previewPort && <span className="text-slate-500">(Port: {previewPort})</span>}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => loadPreviewStatus()}
                className="btn-press flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-400 px-2.5 py-1 text-xs text-slate-300 hover:text-white"
              >
                <RefreshCw className="h-3 w-3" />
                <span>Refresh Logs</span>
              </button>
              <button
                onClick={() => setPreviewLogs([])}
                className="btn-press rounded-lg border border-border-subtle bg-surface-400 px-2.5 py-1 text-xs text-slate-400 hover:text-white"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="rounded-xl bg-black/90 p-4 border border-border-subtle font-mono text-xs text-slate-200 h-[500px] overflow-y-auto space-y-1">
            {previewLogs.length > 0 ? (
              previewLogs.map((logLine, idx) => {
                const isErr = logLine.includes('ERROR') || logLine.includes('Traceback') || logLine.includes('Error:');
                const isWarn = logLine.includes('WARNING') || logLine.includes('WARN');
                return (
                  <div
                    key={idx}
                    className={`leading-relaxed whitespace-pre-wrap ${
                      isErr ? 'text-accent-rose' : isWarn ? 'text-amber-300' : 'text-slate-300'
                    }`}
                  >
                    {logLine}
                  </div>
                );
              })
            ) : (
              <div className="text-slate-500 py-12 text-center">
                Terminal idle. Start the preview server to stream runtime stdout and stderr logs.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 1: AI Workspace Copilot / Chat */}
      {activeTab === 'copilot' && (
        <div className="space-y-4">
          {/* Phase 1.4: Proposed Change Plan Approval Card */}
          {pendingChangePlan && (
            <div className="rounded-2xl border border-amber-500/40 bg-surface-300 p-5 shadow-2xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-500/30">
                    PENDING APPROVAL
                  </span>
                  <span className="text-xs font-bold text-white">Proposed Code & Feature Modifications</span>
                </div>
                <button
                  onClick={handleRejectChangePlan}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  ✕ Dismiss
                </button>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-slate-300 font-medium">
                  {pendingChangePlan.understanding}
                </p>

                <div className="flex flex-wrap gap-2 pt-1">
                  {pendingChangePlan.affected_files?.map((f: string, i: number) => (
                    <span key={i} className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-400 border border-border-subtle text-amber-300">
                      ✎ {f}
                    </span>
                  ))}
                  {pendingChangePlan.new_files?.map((f: string, i: number) => (
                    <span key={i} className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                      + {f}
                    </span>
                  ))}
                </div>

                {pendingChangePlan.features_to_add_or_modify && (
                  <div className="pt-2">
                    <span className="text-[11px] font-semibold text-slate-400 block mb-1">Key Updates:</span>
                    <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                      {pendingChangePlan.features_to_add_or_modify.map((feat: string, i: number) => (
                        <li key={i}>{feat}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {pendingChangePlan.risks_and_breaking_changes && (
                  <div className="text-[11px] text-slate-400 bg-surface-400/40 rounded-lg p-2 border border-border-subtle">
                    <span className="font-semibold text-slate-300">Safety & Validation: </span>
                    {pendingChangePlan.risks_and_breaking_changes.join(', ')}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={handleApproveChangePlan}
                  disabled={isApplyingChange}
                  className="btn-press flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2 shadow-md shadow-emerald-600/20 disabled:opacity-50"
                >
                  <Check className="h-4 w-4" />
                  <span>{isApplyingChange ? 'Applying Changes & Validating Syntax...' : 'Approve & Apply Changes'}</span>
                </button>
                <button
                  onClick={handleRejectChangePlan}
                  disabled={isApplyingChange}
                  className="btn-press rounded-xl bg-surface-400 hover:bg-surface-500 text-slate-300 hover:text-white font-bold text-xs px-4 py-2 border border-border-subtle"
                >
                  Reject Plan
                </button>
              </div>
            </div>
          )}

          {/* Main Chat Box */}
          <div className="rounded-2xl border border-border-subtle bg-surface-300/80 shadow-xl overflow-hidden flex flex-col h-[600px]">
            {/* Chat Header */}
            <div className="p-4 border-b border-border-subtle bg-surface-400/40 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-brand-500 to-accent-purple flex items-center justify-center text-white shadow-md shadow-brand-500/20">
                  <Bot className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
                    <span>AI Lead Architect & Workspace Copilot</span>
                    <span className="rounded bg-accent-emerald/20 text-emerald-300 text-[9px] px-1.5 py-0.2 border border-accent-emerald/30">
                      Grounded
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Collaborate on architecture, generate custom source code, or refine project scope.
                  </p>
                </div>
              </div>

              <button
                onClick={() => handleBuildWorkspace(true)}
                disabled={Boolean(actionLoading)}
                className="btn-press hidden sm:flex items-center gap-1.5 rounded-xl bg-brand-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-brand-500 shadow-sm"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{actionLoading === 'build' ? 'Building...' : '⚡ Generate Code with AI'}</span>
              </button>
            </div>

            {/* Messages Thread */}
            <div ref={chatScrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 font-sans">
              {chatMessages.map((msg) => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    {!isUser && (
                      <div className="h-7 w-7 shrink-0 rounded-lg bg-brand-600/30 border border-brand-500/40 flex items-center justify-center text-brand-300 text-xs">
                        <Bot className="h-3.5 w-3.5" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed shadow-md ${
                        isUser
                          ? 'bg-brand-600 text-white rounded-tr-none'
                          : 'bg-surface-400/90 text-slate-200 border border-border-subtle rounded-tl-none'
                      }`}
                    >
                      <div className="whitespace-pre-wrap font-sans">{msg.content}</div>

                      {/* If AI provided tech stack preview in message */}
                      {msg.suggestedTechStack && (
                        <div className="mt-3 rounded-xl bg-[#090d16] p-3 border border-brand-500/30 space-y-2">
                          <span className="text-[10px] font-bold text-brand-300 uppercase tracking-wider block">
                            Recommended Architecture Stack
                          </span>
                          <div className="grid grid-cols-2 gap-2 text-[11px]">
                            <div>
                              <span className="text-slate-400 block text-[9px] uppercase">Frontend</span>
                              <span className="font-semibold text-white">
                                {Array.isArray(msg.suggestedTechStack.frontend)
                                  ? msg.suggestedTechStack.frontend.join(', ')
                                  : msg.suggestedTechStack.frontend}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-400 block text-[9px] uppercase">Backend</span>
                              <span className="font-semibold text-white">
                                {Array.isArray(msg.suggestedTechStack.backend)
                                  ? msg.suggestedTechStack.backend.join(', ')
                                  : msg.suggestedTechStack.backend}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-400 block text-[9px] uppercase">Database</span>
                              <span className="font-semibold text-white">
                                {msg.suggestedTechStack.database}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-400 block text-[9px] uppercase">Architecture</span>
                              <span className="font-semibold text-white">
                                {msg.suggestedTechStack.architecture}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleApplyTechStack(msg.suggestedTechStack)}
                            className="btn-press mt-2 w-full flex items-center justify-center gap-1.5 rounded-lg bg-brand-600 py-1.5 text-xs font-bold text-white hover:bg-brand-500 shadow-sm"
                          >
                            <Check className="h-3 w-3" />
                            <span>Apply This Tech Stack & Save</span>
                          </button>
                        </div>
                      )}

                      {/* Suggested quick action buttons on message */}
                      {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-border-subtle flex flex-wrap gap-1.5">
                          {msg.suggestedActions.map((action, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                if (action === 'build_workspace' || action.includes('Generate Entire Codebase')) {
                                  handleBuildWorkspace(true);
                                } else if (action === 'update_tech_stack' || action.includes('Tech Stack')) {
                                  handleSuggestTechStack();
                                } else {
                                  handleSendMessage(action);
                                }
                              }}
                              className="btn-press text-[10px] rounded-lg bg-surface-300 hover:bg-surface-200 border border-border-subtle px-2.5 py-1 text-slate-300 font-semibold transition-colors"
                            >
                              {action}
                            </button>
                          ))}
                        </div>
                      )}

                      <div className="mt-1 text-[9px] text-slate-400 text-right opacity-70">
                        {msg.timestamp}
                      </div>
                    </div>
                    {isUser && (
                      <div className="h-7 w-7 shrink-0 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-300 text-xs">
                        <UserIcon className="h-3.5 w-3.5" />
                      </div>
                    )}
                  </div>
                );
              })}

              {chatLoading && (
                <div className="flex gap-3 justify-start items-center">
                  <div className="h-7 w-7 shrink-0 rounded-lg bg-brand-600/30 border border-brand-500/40 flex items-center justify-center text-brand-300 text-xs">
                    <Bot className="h-3.5 w-3.5 animate-spin" />
                  </div>
                  <div className="rounded-2xl rounded-tl-none bg-surface-400/90 border border-border-subtle p-3 text-xs text-slate-300 flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
                    </span>
                    <span>AI Copilot is analyzing codebase & crafting response...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Prompt Chips */}
            <div className="px-4 py-2 border-t border-border-subtle bg-surface-400/20 overflow-x-auto flex items-center gap-1.5">
              {[
                '⚡ Generate full codebase with AI',
                '🛠️ Change tech stack to Next.js & PostgreSQL',
                '📐 Add new schema entities for billing',
                '🧪 What tests are implemented?',
              ].map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    if (chip.startsWith('⚡')) {
                      handleBuildWorkspace(true);
                    } else {
                      handleSendMessage(chip);
                    }
                  }}
                  className="btn-press whitespace-nowrap text-[11px] rounded-full border border-border-subtle bg-surface-400/60 hover:bg-surface-400 px-3 py-1 text-slate-300 hover:text-white transition-colors"
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="p-3 border-t border-border-subtle bg-surface-400/50">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask Copilot: 'Add user authentication', 'Change backend to Go', 'Generate the code'..."
                  disabled={chatLoading}
                  className="flex-1 rounded-xl border border-border-subtle bg-surface-300 px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
                />
                <button
                  type="submit"
                  disabled={chatLoading || !chatInput.trim()}
                  className="btn-press flex items-center justify-center h-9 w-9 rounded-xl bg-brand-600 text-white hover:bg-brand-500 disabled:opacity-40 transition-colors shrink-0"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          </div>

          {/* Phase 1.4: Version History & Snapshot Rollback Drawer */}
          {changeHistory.length > 0 && (
            <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Undo2 className="h-4 w-4 text-brand-400" />
                  <h4 className="text-xs font-bold text-white">Project Version History & Snapshots</h4>
                  <span className="rounded-full bg-surface-400 px-2 py-0.5 text-[10px] text-slate-400">
                    {changeHistory.length} snapshots
                  </span>
                </div>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto">
                {changeHistory.slice().reverse().map((snap: any, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl bg-surface-400/50 border border-border-subtle text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-brand-300 text-[11px]">v{snap.version}</span>
                        <span className="text-white font-medium">{snap.instruction}</span>
                      </div>
                      <span className="text-[10px] text-slate-400">
                        {new Date(snap.timestamp).toLocaleString()} • {snap.files_backed_up?.length || 0} files backed up
                      </span>
                    </div>

                    <button
                      onClick={() => handleRollbackVersion(snap.version)}
                      disabled={isRollingBack}
                      className="btn-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-200 text-slate-300 hover:text-white text-[11px] font-semibold border border-border-subtle"
                    >
                      <RotateCw className="h-3 w-3" />
                      <span>Rollback to v{snap.version}</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Blueprint Content */}
      {activeTab === 'blueprint' && (
        <div className="space-y-6">
          {/* AI Re-Architect Control Panel */}
          <div className="rounded-2xl border border-brand-500/30 bg-gradient-to-r from-surface-300 via-surface-300/95 to-brand-950/20 p-5 space-y-4 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 border border-brand-500/30">
                    AI ARCHITECT ENGINE
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Dynamic System Synthesis</span>
                </div>
                <h3 className="text-sm font-bold text-white mt-1">
                  Re-Architect Blueprint with AI
                </h3>
                <p className="text-xs text-slate-300">
                  Select a stack preset or provide custom requirements to re-synthesize system layers, schemas, and API contracts.
                </p>
              </div>

              <button
                onClick={() => handleRearchitect()}
                disabled={rearchitecting}
                className="btn-press flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white hover:bg-brand-500 disabled:opacity-50 shrink-0 shadow-md shadow-brand-500/20"
              >
                <Sparkles className={`h-3.5 w-3.5 ${rearchitecting ? 'animate-spin' : ''}`} />
                <span>{rearchitecting ? 'Re-Architecting...' : '🤖 Re-Architect Blueprint with AI'}</span>
              </button>
            </div>

            {/* Quick Stack Presets */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[11px] text-slate-400 font-semibold mr-1">Presets:</span>
              {[
                {
                  label: 'Next.js 14 + FastAPI + PostgreSQL',
                  stack: {
                    frontend: ['Next.js 14 App Router', 'Tailwind CSS'],
                    backend: ['FastAPI Async Framework', 'Pydantic V2 Models'],
                    database: 'PostgreSQL Async with SQLAlchemy 2.0',
                    architecture: 'Modular Monolith / REST API',
                  },
                },
                {
                  label: 'React + Node Express + MongoDB',
                  stack: {
                    frontend: ['React 18', 'Tailwind CSS'],
                    backend: ['Node.js', 'Express REST API'],
                    database: 'MongoDB with Mongoose ODM',
                    architecture: 'MERN Micro-modular API',
                  },
                },
                {
                  label: 'Django REST + Vue 3 + PostgreSQL',
                  stack: {
                    frontend: ['Vue 3 Composition API', 'Vite'],
                    backend: ['Python 3.11', 'Django REST Framework'],
                    database: 'PostgreSQL Relational DB',
                    architecture: 'Layered Enterprise Architecture',
                  },
                },
                {
                  label: 'Go Fiber + Next.js + Redis',
                  stack: {
                    frontend: ['Next.js 14', 'TypeScript'],
                    backend: ['Go (Golang)', 'Fiber High-Perf HTTP'],
                    database: 'PostgreSQL + Redis In-Memory Cache',
                    architecture: 'High-Throughput Microservice',
                  },
                },
              ].map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleRearchitect(undefined, p.stack)}
                  disabled={rearchitecting}
                  className="btn-press text-[11px] rounded-lg border border-border-subtle bg-surface-400/80 hover:bg-surface-400 hover:border-brand-500/50 px-2.5 py-1 text-slate-300 hover:text-white transition-colors"
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Custom Instruction Input */}
            <div className="flex items-center gap-2 pt-1">
              <input
                type="text"
                value={rearchitectPrompt}
                onChange={(e) => setRearchitectPrompt(e.target.value)}
                placeholder="Optional custom instructions: e.g. 'Add Redis cache layer, WebSocket support, OAuth2 token verification'..."
                className="flex-1 rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleRearchitect(rearchitectPrompt);
                  }
                }}
              />
              <button
                onClick={() => handleRearchitect(rearchitectPrompt)}
                disabled={rearchitecting}
                className="btn-press rounded-xl border border-brand-500/40 bg-brand-500/20 px-3 py-2 text-xs font-bold text-brand-300 hover:bg-brand-500/30"
              >
                Apply
              </button>
            </div>
          </div>

          {blueprint ? (
            <div className="space-y-6">
              {/* Architecture Layers Overview if present */}
              {blueprint.architecture && (
                <div className="rounded-2xl border border-border-subtle bg-surface-300/70 p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-bold text-white">
                      <Layers className="h-4 w-4 text-brand-400" />
                      <span>Synthesized System Architecture Layers</span>
                    </div>
                    {blueprint.architecture.pattern && (
                      <span className="rounded-full bg-brand-500/20 border border-brand-500/30 px-2.5 py-0.5 text-[10px] font-mono font-bold text-brand-300">
                        {blueprint.architecture.pattern}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="rounded-xl border border-border-subtle bg-surface-400/70 p-3 space-y-1">
                      <span className="text-[10px] font-bold text-brand-300 uppercase tracking-wider block">
                        1. Frontend Layer
                      </span>
                      <p className="text-[11px] text-slate-300 leading-relaxed">
                        {blueprint.architecture.frontend_layer || 'Reactive UI and presentation components.'}
                      </p>
                    </div>

                    <div className="rounded-xl border border-border-subtle bg-surface-400/70 p-3 space-y-1">
                      <span className="text-[10px] font-bold text-accent-cyan uppercase tracking-wider block">
                        2. API Gateway Layer
                      </span>
                      <p className="text-[11px] text-slate-300 leading-relaxed">
                        {blueprint.architecture.api_gateway_layer || 'REST boundary, middleware, routing and auth filters.'}
                      </p>
                    </div>

                    <div className="rounded-xl border border-border-subtle bg-surface-400/70 p-3 space-y-1">
                      <span className="text-[10px] font-bold text-accent-emerald uppercase tracking-wider block">
                        3. Domain Service Layer
                      </span>
                      <p className="text-[11px] text-slate-300 leading-relaxed">
                        {blueprint.architecture.service_layer || 'Core business validation rules and data transformation logic.'}
                      </p>
                    </div>

                    <div className="rounded-xl border border-border-subtle bg-surface-400/70 p-3 space-y-1">
                      <span className="text-[10px] font-bold text-accent-purple uppercase tracking-wider block">
                        4. Persistence Layer
                      </span>
                      <p className="text-[11px] text-slate-300 leading-relaxed">
                        {blueprint.architecture.data_layer || 'Relational schema indexing, connection pools, and ORM.'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Data Models */}
              <div className="rounded-2xl border border-border-subtle bg-surface-300/70 p-5">
                <div className="flex items-center gap-2 text-sm font-bold text-white mb-3">
                  <Database className="h-4 w-4 text-accent-cyan" />
                  <span>Database Schema Entities</span>
                </div>
                {blueprint.database_schema && blueprint.database_schema.length > 0 ? (
                  <div className="space-y-3">
                    {blueprint.database_schema.map((m: any, idx: number) => (
                      <div key={idx} className="rounded-xl bg-surface-400/80 p-3 border border-border-subtle">
                        <div className="text-xs font-bold text-accent-cyan">{m.table || m.name}</div>
                        <div className="text-[11px] text-slate-400 mt-1">{m.purpose || m.description}</div>
                        {m.columns && (
                          <div className="mt-2 text-[10px] font-mono text-slate-300 bg-black/40 p-2 rounded">
                            {Array.isArray(m.columns) ? m.columns.join(' | ') : JSON.stringify(m.columns)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : blueprint.data_models && blueprint.data_models.length > 0 ? (
                  <div className="space-y-3">
                    {blueprint.data_models.map((m: any, idx: number) => (
                      <div key={idx} className="rounded-xl bg-surface-400/80 p-3 border border-border-subtle">
                        <div className="text-xs font-bold text-accent-cyan">{m.name}</div>
                        <div className="text-[11px] text-slate-400 mt-1">{m.description}</div>
                        {m.fields && (
                          <div className="mt-2 text-[10px] font-mono text-slate-300 bg-black/40 p-2 rounded">
                            {Array.isArray(m.fields) ? m.fields.join(', ') : JSON.stringify(m.fields)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">Standard relational schema models initialized.</p>
                )}
              </div>

              {/* API Endpoints */}
              <div className="rounded-2xl border border-border-subtle bg-surface-300/70 p-5">
                <div className="flex items-center gap-2 text-sm font-bold text-white mb-3">
                  <Terminal className="h-4 w-4 text-accent-emerald" />
                  <span>REST API Contracts</span>
                </div>
                {blueprint.api_endpoints && blueprint.api_endpoints.length > 0 ? (
                  <div className="space-y-2">
                    {blueprint.api_endpoints.map((ep: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-xl bg-surface-400/80 p-2.5 border border-border-subtle text-xs font-mono"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              ep.method === 'GET'
                                ? 'bg-blue-500/20 text-blue-300'
                                : 'bg-emerald-500/20 text-emerald-300'
                            }`}
                          >
                            {ep.method}
                          </span>
                          <span className="text-slate-200">{ep.path}</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-sans">{ep.description || ep.purpose}</span>
                      </div>
                    ))}
                  </div>
                ) : blueprint.api_contracts && blueprint.api_contracts.length > 0 ? (
                  <div className="space-y-2">
                    {blueprint.api_contracts.map((ep: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-xl bg-surface-400/80 p-2.5 border border-border-subtle text-xs font-mono"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              ep.method === 'GET'
                                ? 'bg-blue-500/20 text-blue-300'
                                : 'bg-emerald-500/20 text-emerald-300'
                            }`}
                          >
                            {ep.method}
                          </span>
                          <span className="text-slate-200">{ep.path}</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-sans">{ep.purpose || ep.description}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">Endpoints formulated during synthesis stage.</p>
                )}
              </div>
            </div>
          </div>
          ) : (
            <div className="rounded-2xl border border-border-subtle bg-surface-300/40 p-8 text-center text-xs text-slate-400">
              Blueprint is being generated or was created via standard direct pipeline.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Files Content */}
      {activeTab === 'files' && (
        <div className="rounded-2xl border border-border-subtle bg-surface-300/70 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode className="h-4 w-4 text-brand-400" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Workspace Source Files ({project.files?.length || 0})
              </span>
            </div>
            <button
              onClick={() => handleBuildWorkspace(true)}
              disabled={Boolean(actionLoading)}
              className="btn-press flex items-center gap-1.5 rounded-xl bg-brand-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-brand-500 shadow-sm"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>{actionLoading === 'build' ? 'Synthesizing...' : '⚡ Regenerate with AI'}</span>
            </button>
          </div>

          {project.files && project.files.length > 0 ? (
            <div className="space-y-3">
              {project.files.map((f, idx) => (
                <div key={idx} className="rounded-xl border border-border-subtle bg-surface-400/80 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-brand-300">{f.path}</span>
                    <span className="text-[11px] text-slate-400">{f.purpose || 'Component'}</span>
                  </div>
                  {f.content && (
                    <pre className="max-h-56 overflow-y-auto rounded-lg bg-black/60 p-3 font-mono text-[11px] text-slate-300">
                      <code>{f.content}</code>
                    </pre>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-xs text-slate-400 space-y-3">
              <p>No files written to workspace yet.</p>
              <button
                onClick={() => handleBuildWorkspace(true)}
                disabled={Boolean(actionLoading)}
                className="btn-press inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white hover:bg-brand-500"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Synthesize Entire Codebase with AI Now</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Test & Verification Content */}
      {activeTab === 'test' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-6 space-y-6 shadow-xl">
            {/* Header and Trigger */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-5">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-accent-emerald/20 px-2 py-0.5 text-[10px] font-bold text-accent-emerald border border-accent-emerald/30">
                    AUTOMATED TEST SUITE
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Isolated Pytest Runner</span>
                </div>
                <h3 className="text-base font-bold text-white mt-1">
                  Automated Sandbox Pytest & Assertion Verification
                </h3>
                <p className="text-xs text-slate-300">
                  Executes live automated tests against the synthesized backend in an isolated sandbox process to prove functionality.
                </p>
              </div>

              <button
                onClick={handleTestWorkspace}
                disabled={actionLoading === 'test'}
                className="btn-press flex items-center gap-2 rounded-xl bg-accent-emerald px-4 py-2.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 shrink-0 shadow-lg shadow-emerald-500/20"
              >
                <FlaskConical className={`h-4 w-4 ${actionLoading === 'test' ? 'animate-spin' : ''}`} />
                <span>{actionLoading === 'test' ? 'Executing Pytest in Sandbox...' : 'Run Pytest Test Suite'}</span>
              </button>
            </div>

            {/* Metrics Overview Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="rounded-xl border border-border-subtle bg-surface-400/80 p-3.5 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Verification Status
                </span>
                <div className="flex items-center gap-2 mt-0.5">
                  {testResults?.passed ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-accent-emerald" />
                      <span className="text-xs font-bold text-accent-emerald">PASSING</span>
                    </>
                  ) : testResults?.passed === false ? (
                    <>
                      <XCircle className="h-4 w-4 text-accent-rose" />
                      <span className="text-xs font-bold text-accent-rose">FAILING</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 text-brand-400" />
                      <span className="text-xs font-bold text-slate-300">NOT RUN YET</span>
                    </>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-border-subtle bg-surface-400/80 p-3.5 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Tests Passed
                </span>
                <div className="text-base font-black text-white mt-0.5">
                  {testResults?.tests_passed ?? (testResults?.passed ? 4 : 0)} Passed
                </div>
              </div>

              <div className="rounded-xl border border-border-subtle bg-surface-400/80 p-3.5 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Tests Failed
                </span>
                <div className="text-base font-black text-white mt-0.5">
                  {testResults?.tests_failed ?? 0} Failed
                </div>
              </div>

              <div className="rounded-xl border border-border-subtle bg-surface-400/80 p-3.5 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Process Returncode
                </span>
                <div className="text-base font-black text-white mt-0.5 font-mono">
                  code {testResults?.returncode ?? 0}
                </div>
              </div>
            </div>

            {/* Real Monospace Terminal Log Viewer */}
            <div className="rounded-xl border border-slate-700/80 bg-[#090d16] shadow-2xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 text-xs">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="h-3 w-3 rounded-full bg-rose-500/80" />
                    <div className="h-3 w-3 rounded-full bg-amber-500/80" />
                    <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
                  </div>
                  <span className="text-[11px] font-mono text-slate-400 ml-2">
                    sandbox/test_suite.py &bull; pytest runner
                  </span>
                </div>
                {testResults?.executed_at && (
                  <span className="text-[10px] font-mono text-slate-500">
                    {testResults.executed_at}
                  </span>
                )}
              </div>

              <div className="p-4 font-mono text-xs leading-relaxed max-h-96 overflow-y-auto">
                {testResults?.stdout ? (
                  <pre className="text-emerald-300/90 whitespace-pre-wrap font-mono">
                    {testResults.stdout}
                  </pre>
                ) : testResults?.stderr ? (
                  <pre className="text-rose-300/90 whitespace-pre-wrap font-mono">
                    {testResults.stderr}
                  </pre>
                ) : (
                  <div className="text-slate-500 space-y-1 py-2">
                    <p className="text-slate-400">$ pytest test_suite.py -v --tb=short</p>
                    <p>&gt; Ready to execute test verification in sandbox.</p>
                    <p>&gt; Click &apos;Run Pytest Test Suite&apos; above to verify API contracts and schema validation.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Test Coverage Specifications */}
            <div className="rounded-xl border border-border-subtle bg-surface-400/50 p-4 space-y-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider block">
                Verification Assurances
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <span className="text-accent-emerald font-bold">&check;</span>
                  <span>Health Check: GET / status and service identification</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-accent-emerald font-bold">&check;</span>
                  <span>Data Ingestion: POST /api/items validation &amp; payload parsing</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-accent-emerald font-bold">&check;</span>
                  <span>Schema Contracts: Pydantic response models &amp; types</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-accent-emerald font-bold">&check;</span>
                  <span>Error Boundaries: 404/422 HTTP exception resilience</span>
                </div>
              </div>
            </div>
          </div>

          {/* Phase 1.4: Version History & Snapshot Rollback Drawer */}
          {changeHistory.length > 0 && (
            <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Undo2 className="h-4 w-4 text-brand-400" />
                  <h4 className="text-xs font-bold text-white">Project Version History & Snapshots</h4>
                  <span className="rounded-full bg-surface-400 px-2 py-0.5 text-[10px] text-slate-400">
                    {changeHistory.length} snapshots
                  </span>
                </div>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto">
                {changeHistory.slice().reverse().map((snap: any, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl bg-surface-400/50 border border-border-subtle text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-brand-300 text-[11px]">v{snap.version}</span>
                        <span className="text-white font-medium">{snap.instruction}</span>
                      </div>
                      <span className="text-[10px] text-slate-400">
                        {new Date(snap.timestamp).toLocaleString()} • {snap.files_backed_up?.length || 0} files backed up
                      </span>
                    </div>

                    <button
                      onClick={() => handleRollbackVersion(snap.version)}
                      disabled={isRollingBack}
                      className="btn-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-300 hover:bg-surface-200 text-slate-300 hover:text-white text-[11px] font-semibold border border-border-subtle"
                    >
                      <RotateCw className="h-3 w-3" />
                      <span>Rollback to v{snap.version}</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Teaching Content */}
      {activeTab === 'teaching' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border-subtle bg-surface-300/80 p-5 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white">Ask AI Teacher About This Project</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Explanations are dynamically grounded in the actual generated files of {project.title || project.name}.
              </p>
            </div>

            <form onSubmit={handleAskTeacher} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <input
                    type="text"
                    value={teachTopic}
                    onChange={(e) => setTeachTopic(e.target.value)}
                    placeholder="e.g. Async FastAPI Event Loop, Schema validation, Database connection pooling"
                    className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                    required
                  />
                </div>
                <div>
                  <select
                    value={teachLevel}
                    onChange={(e) => setTeachLevel(e.target.value)}
                    className="w-full rounded-xl border border-border-subtle bg-surface-400 px-3 py-2 text-xs font-semibold text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="interview_prep">Interview Prep</option>
                    <option value="advanced">Advanced Systems</option>
                    <option value="intermediate">Intermediate Implementation</option>
                    <option value="beginner">Beginner Fundamentals</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={teachLoading}
                className="btn-press flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white hover:bg-brand-500 disabled:opacity-50"
              >
                <GraduationCap className="h-3.5 w-3.5" />
                <span>{teachLoading ? 'Analyzing Codebase & Synthesizing...' : 'Explain In Project Context &rarr;'}</span>
              </button>
            </form>
          </div>

          {teachExplanation && (
            <div className="rounded-2xl border border-brand-500/30 bg-surface-300/90 p-6 space-y-4 shadow-xl">
              <div className="flex items-center gap-2">
                <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[10px] font-bold text-brand-300 uppercase">
                  {teachExplanation.level || teachLevel}
                </span>
                <h4 className="text-sm font-bold text-white">{teachExplanation.topic}</h4>
              </div>

              <p className="text-xs text-slate-200 leading-relaxed font-sans">{teachExplanation.summary}</p>

              {teachExplanation.interview_explanation && (
                <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 p-4">
                  <div className="text-[10px] font-bold uppercase text-amber-300 mb-1">
                    Interview Explanation Strategy
                  </div>
                  <p className="text-xs italic text-amber-100">&ldquo;{teachExplanation.interview_explanation}&rdquo;</p>
                </div>
              )}

              {teachExplanation.under_the_hood && (
                <div className="rounded-xl border border-border-subtle bg-surface-400/70 p-4 text-xs text-slate-300">
                  <strong className="text-accent-cyan block mb-1">Under The Hood & Internals:</strong>
                  {teachExplanation.under_the_hood}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
