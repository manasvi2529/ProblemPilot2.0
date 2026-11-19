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

export interface Project {
  id: string;
  name?: string;
  title: string;
  description: string;
  repository_name?: string;
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

export interface ResearchSession {
  id: string;
  query: string;
  platforms?: string[];
  sources?: any[];
  problems?: ProblemOpportunity[];
  created_at?: string;
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
