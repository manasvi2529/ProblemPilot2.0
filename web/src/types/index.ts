export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  name?: string;
  operating_mode: 'autonomous' | 'guided' | 'hybrid';
  is_active: boolean;
  github_connected?: boolean;
  github_username?: string | null;
  preferences?: Record<string, any>;
  created_at?: string;
}

export interface ProblemOpportunity {
  id: string;
  title: string;
  description?: string;
  summary?: string;
  target_audience?: string;
  target_user?: string;
  domain?: string;
  category?: string;
  severity?: string;
  urgency?: string;
  viability_score?: number;
  confidence_score?: number;
  overall_score?: number;
  commercial_viability?: number;
  technical_complexity?: string;
  complexity?: string;
  market_gap?: string;
  monetization_potential?: string;
  monetization?: string;
  tags?: string[];
  evidence_citations?: string[];
  evidence_count?: number;
  pillar_breakdown?: {
    pillar_a_market_demand?: number;
    pillar_b_technical_feasibility?: number;
    pillar_c_developer_moat?: number;
  };
}

export interface TechStackSelection {
  frontend: string;
  backend: string;
  database: string;
  architecture: string;
  customNotes?: string;
}

export interface ProjectFile {
  path: string;
  purpose?: string;
  content?: string;
}

export interface ResearchIntelligence {
  report_id?: string;
  session_id?: string;
  opportunity_title?: string;
  underserved_need?: string;
  proposed_solution?: string;
  overall_score?: number;
  evidence_sufficiency?: string;
  search_provider?: string;
  pain_points_addressed?: Array<{
    pain_point: string;
    evidence_quote?: string;
    severity?: string;
    feature_solution?: string;
  }>;
  competitor_gaps_exploited?: Array<{
    competitor: string;
    competitor_gap: string;
    our_advantage: string;
  }>;
  pricing_strategy?: string;
  citations?: Array<{
    title: string;
    url: string;
    publisher?: string;
    claim_type?: string;
    retrieval_date?: string;
  }>;
  actionable_recommendations?: any[];
  risks_and_limitations?: any[];
}

export interface Project {
  id: string;
  name?: string;
  title: string;
  description: string;
  repository_name?: string;
  research_report_id?: string;
  current_stage: 'discover' | 'architect' | 'build' | 'test' | 'teach' | 'deploy' | 'complete';
  status: string;
  tech_stack?: Record<string, any>;
  custom_instructions?: string;
  blueprint?: Record<string, any>;
  files?: ProjectFile[];
  created_at?: string;
  updated_at?: string;
}

export interface Approval {
  id: string;
  project_id: string;
  stage: string;
  action: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected';
  reason?: string;
  metadata?: Record<string, any>;
  created_at?: string;
  decided_at?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  suggestedActions?: string[];
  suggestedTechStack?: Record<string, any>;
  isGenerating?: boolean;
}

export interface SystemHealth {
  status: string;
  service: string;
  integrations: {
    ai: {
      configured: boolean;
      provider: string;
      google_studio_configured?: boolean;
      openrouter_configured?: boolean;
    };
    search: { configured: boolean; provider: string };
    github: { configured: boolean };
  };
}

export type SearchMode = 'live' | 'mixed' | 'curated_fallback';

export interface ResearchSourceItem {
  id?: string;
  url: string;
  title: string;
  publisher?: string;
  snippet?: string;
  raw_snippet?: string;
  full_text?: string;
  publication_date?: string | null;
  retrieval_date?: string;
  claim_type?: 'verified_fact' | 'source_backed' | 'inference' | 'hypothesis' | string;
  reliability?: string;
  provider?: string;
  is_live?: boolean;
  content_extracted?: boolean;
  retrieval_status?: 'success' | 'snippet_only' | 'failed' | string;
  extraction_error?: string | null;
  supporting_passage?: string;
}

export interface ResearchSession {
  id: string;
  query: string;
  domain?: string;
  geography?: string;
  target_users?: string;
  status?: string;
  progress_pct?: number;
  current_step?: string;
  step_message?: string;
  used_live_search?: boolean;
  search_provider?: string;
  search_mode?: SearchMode;
  providers_attempted?: string[];
  providers_diagnostics?: Record<string, any>;
  failover_occurred?: boolean;
  error_message?: string;
  platforms?: string[];
  sources?: ResearchSourceItem[];
  problems?: ProblemOpportunity[];
  created_at?: string;
  completed_at?: string;
}

export interface ResearchSessionStatus {
  session_id: string;
  status: 'queued' | 'searching' | 'extracting' | 'analyzing' | 'scoring' | 'completed' | 'failed' | 'cancelled' | string;
  progress_pct: number;
  current_step: string;
  step_message: string;
  error_message?: string | null;
  used_live_search: boolean;
  search_provider?: string | null;
  search_mode?: SearchMode;
  providers_attempted?: string[];
  providers_diagnostics?: Record<string, any>;
  failover_occurred?: boolean;
  has_report: boolean;
  created_at?: string | null;
  completed_at?: string | null;
}

export interface DeploymentRecord {
  id: string;
  project_id: string;
  provider: string;
  deployment_url?: string;
  status: string;
  health_check_result?: {
    verified: boolean;
    status_code?: number;
    response_time_ms?: number;
  };
  created_at?: string;
}

export interface TeacherExplanation {
  topic: string;
  level: string;
  summary: string;
  what_it_is?: string;
  why_used?: string;
  how_it_works?: string;
  mental_model?: string;
  how_it_works_here?: string;
  under_the_hood?: string;
  architecture_connection?: string;
  alternatives_and_tradeoffs?: Array<{ alternative?: string; tradeoff?: string; [key: string]: any }>;
  common_pitfalls?: Array<string | { mistake?: string; pitfall?: string; avoidance?: string; solution?: string; [key: string]: any }>;
  how_to_test?: string;
  practical_exercises?: Array<{ exercise?: string; hint?: string; [key: string]: any }>;
  interview_explanation?: string;
  what_to_learn_next?: Array<string | { topic?: string; title?: string; [key: string]: any }>;
}

export interface AuditLogItem {
  id: string;
  user_id?: string;
  project_id?: string;
  action: string;
  category: string;
  description: string;
  details?: Record<string, any>;
  status: string;
  error_message?: string;
  created_at?: string;
}

export interface IntegrationsStatus {
  callback_url: string;
  ai: {
    configured: boolean;
    provider: string;
    model?: string;
    google_studio_configured?: boolean;
    openrouter_configured?: boolean;
  };
  search: {
    configured: boolean;
    provider: string;
    canonical_search_mode?: SearchMode;
    message?: string;
    diagnostics?: {
      configured_mode?: string;
      has_live_credentials?: boolean;
      providers?: Record<string, {
        available: boolean;
        masked_key?: string | null;
        role?: string;
        engine_id_configured?: boolean;
      }>;
    };
  };
  github: {
    configured: boolean;
    oauth_enabled: boolean;
    missing_vars?: string[];
    connected: boolean;
    status: string;
    username?: string | null;
    connected_at?: string | null;
    callback_url?: string;
  };
  cloud: {
    vercel?: {
      configured?: boolean;
      missing_vars?: string[];
      status?: string;
      expected_cost?: string;
      deploy_methods?: string[];
    };
    render?: {
      configured?: boolean;
      status?: string;
      expected_cost?: string;
      deploy_methods?: string[];
    };
    docker?: {
      status?: string;
    };
  };
}


export interface BenchmarkCase {
  id: string;
  version: string;
  category: string;
  title: string;
  description: string;
  expected_domain_entities: string[];
  known_competitors: string[];
  sha256_digest: string;
}

export interface BenchmarkRunRecord {
  id: string;
  owner_id: string;
  project_id?: string | null;
  suite_name: string;
  suite_version: string;
  status: string;
  overall_status: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  average_score: number;
  research_avg_score: number;
  blueprint_avg_score: number;
  app_avg_score: number;
  passed_all_critical_gates: boolean;
  sha256_report_digest?: string;
  report_data?: Record<string, any>;
  created_at: string;
  completed_at?: string;
  case_results?: EvaluationCaseResult[];
}

export interface EvaluationCaseResult {
  id: string;
  benchmark_run_id: string;
  case_id: string;
  case_version: string;
  case_digest?: string;
  status: string;
  overall_score: number;
  research_score: number;
  blueprint_score: number;
  app_score: number;
  passed_all_gates: boolean;
  duration_seconds: number;
  gate_summary?: Record<string, any>;
  research_result?: Record<string, any>;
  blueprint_result?: Record<string, any>;
  app_result?: Record<string, any>;
  created_at: string;
}
