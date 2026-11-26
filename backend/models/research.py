"""Research models — sessions, sources, and evidence."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base, safe_iso


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(200), default="")
    target_users: Mapped[str] = mapped_column(Text, default="")
    geography: Mapped[str] = mapped_column(String(200), default="")
    constraints: Mapped[str] = mapped_column(Text, default="")

    # Status: queued | searching | extracting | analyzing | scoring | completed | failed | cancelled
    status: Mapped[str] = mapped_column(String(30), default="queued")
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String(100), default="queued")
    step_message: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Whether live search was used or fallback
    used_live_search: Mapped[bool] = mapped_column(default=False)
    search_provider: Mapped[str] = mapped_column(String(50), nullable=True)

    # Phase 1.7 search mode contract & provider diagnostics
    search_mode: Mapped[str] = mapped_column(String(30), default="curated_fallback")  # live | mixed | curated_fallback
    providers_attempted: Mapped[list] = mapped_column(JSON, default=list)
    providers_diagnostics: Mapped[dict] = mapped_column(JSON, default=dict)
    failover_occurred: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="research_sessions")
    sources = relationship("ResearchSource", back_populates="session", cascade="all, delete-orphan")
    problems = relationship("ProblemCandidate", back_populates="session", cascade="all, delete-orphan")
    report = relationship("ResearchReport", back_populates="session", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        # Safely count without triggering async lazy-load if not eagerly loaded
        sources_list = self.__dict__.get("sources")
        problems_list = self.__dict__.get("problems")
        source_count = len(sources_list) if (sources_list is not None and hasattr(sources_list, '__len__')) else 0
        problem_count = len(problems_list) if (problems_list is not None and hasattr(problems_list, '__len__')) else 0

        return {
            "id": self.id,
            "query": self.query,
            "domain": self.domain,
            "target_users": self.target_users,
            "geography": self.geography,
            "status": self.status,
            "progress_pct": getattr(self, "progress_pct", 0) or 0,
            "current_step": getattr(self, "current_step", "") or "",
            "step_message": getattr(self, "step_message", "") or "",
            "used_live_search": self.used_live_search,
            "search_provider": self.search_provider,
            "search_mode": getattr(self, "search_mode", "curated_fallback") or "curated_fallback",
            "providers_attempted": getattr(self, "providers_attempted", []) or [],
            "providers_diagnostics": getattr(self, "providers_diagnostics", {}) or {},
            "failover_occurred": getattr(self, "failover_occurred", False) or False,
            "error_message": self.error_message,
            "created_at": safe_iso(self.created_at),
            "completed_at": safe_iso(self.completed_at),
            "source_count": source_count,
            "problem_count": problem_count,
        }


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, default="")
    publisher: Mapped[str] = mapped_column(String(300), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    full_text: Mapped[str] = mapped_column(Text, default="")
    publication_date: Mapped[str] = mapped_column(String(50), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    reliability: Mapped[str] = mapped_column(String(30), default="unassessed")  # high | medium | low | unassessed
    source_type: Mapped[str] = mapped_column(String(50), default="web")  # web | report | dataset | discussion | news
    limitations: Mapped[str] = mapped_column(Text, default="")
    key_findings: Mapped[str] = mapped_column(Text, default="")

    # Phase 1.7 provider, extraction & provenance tracking
    provider: Mapped[str] = mapped_column(String(50), default="unknown")  # serper | brave | google_custom | fallback
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    content_extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_snippet: Mapped[str] = mapped_column(Text, default="")
    retrieval_status: Mapped[str] = mapped_column(String(30), default="success")  # success | snippet_only | failed
    extraction_error: Mapped[str] = mapped_column(Text, nullable=True)
    supporting_passage: Mapped[str] = mapped_column(Text, default="")

    session = relationship("ResearchSession", back_populates="sources")

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "publisher": self.publisher,
            "snippet": self.snippet,
            "publication_date": self.publication_date,
            "retrieved_at": safe_iso(self.retrieved_at),
            "relevance_score": self.relevance_score,
            "reliability": self.reliability,
            "source_type": self.source_type,
            "key_findings": self.key_findings,
            "limitations": self.limitations,
            "provider": getattr(self, "provider", "unknown") or "unknown",
            "is_live": getattr(self, "is_live", False) or False,
            "content_extracted": getattr(self, "content_extracted", False) or False,
            "raw_snippet": getattr(self, "raw_snippet", "") or "",
            "retrieval_status": getattr(self, "retrieval_status", "success") or "success",
            "extraction_error": getattr(self, "extraction_error", None),
            "supporting_passage": getattr(self, "supporting_passage", "") or "",
        }


class ProblemCandidate(Base):
    __tablename__ = "problem_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    affected_users: Mapped[str] = mapped_column(Text, default="")
    existing_solutions: Mapped[str] = mapped_column(Text, default="")
    solution_gaps: Mapped[str] = mapped_column(Text, default="")
    evidence_summary: Mapped[str] = mapped_column(Text, default="")

    # Transparent scoring — each dimension 0-10 with explanations
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    # Structure: {"severity": {"score": 7, "explanation": "...", "confidence": "medium"},  ...}
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    score_weights: Mapped[dict] = mapped_column(JSON, default=dict)

    # Evidence tracking
    source_ids: Mapped[list] = mapped_column(JSON, default=list)  # IDs of supporting sources
    evidence_gaps: Mapped[list] = mapped_column(JSON, default=list)
    contradictions: Mapped[list] = mapped_column(JSON, default=list)

    # Claim types
    claim_type: Mapped[str] = mapped_column(String(30), default="inference")
    # verified_fact | source_backed | inference | hypothesis

    # Status: identified | evaluated | selected | rejected
    status: Mapped[str] = mapped_column(String(20), default="identified")
    rank: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ResearchSession", back_populates="problems")
    project = relationship("Project", back_populates="problem", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "affected_users": self.affected_users,
            "existing_solutions": self.existing_solutions,
            "solution_gaps": self.solution_gaps,
            "evidence_summary": self.evidence_summary,
            "scores": self.scores or {},
            "overall_score": self.overall_score,
            "evidence_gaps": self.evidence_gaps or [],
            "contradictions": self.contradictions or [],
            "claim_type": self.claim_type,
            "status": self.status,
            "rank": self.rank,
            "source_ids": self.source_ids or [],
            "created_at": safe_iso(self.created_at),
        }


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # 13 Structured Report Sections
    executive_summary: Mapped[str] = mapped_column(Text, default="")
    problem_landscape: Mapped[dict] = mapped_column(JSON, default=dict)
    target_audience: Mapped[dict] = mapped_column(JSON, default=dict)
    customer_pain_points: Mapped[list] = mapped_column(JSON, default=list)
    competitor_analysis: Mapped[list] = mapped_column(JSON, default=list)
    competitor_pricing: Mapped[dict] = mapped_column(JSON, default=dict)
    market_trends: Mapped[list] = mapped_column(JSON, default=list)
    identified_opportunities: Mapped[list] = mapped_column(JSON, default=list)
    opportunity_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    risks_and_limitations: Mapped[list] = mapped_column(JSON, default=list)
    actionable_recommendations: Mapped[list] = mapped_column(JSON, default=list)
    final_conclusion: Mapped[str] = mapped_column(Text, default="")
    sources: Mapped[list] = mapped_column(JSON, default=list)

    # Meta & Quality Ratings
    evidence_sufficiency: Mapped[str] = mapped_column(String(30), default="moderate")  # high | moderate | insufficient
    used_live_search: Mapped[bool] = mapped_column(default=False)
    search_provider: Mapped[str] = mapped_column(String(50), nullable=True)

    # Phase 1.7 canonical search mode & diagnostics
    search_mode: Mapped[str] = mapped_column(String(30), default="curated_fallback")  # live | mixed | curated_fallback
    providers_diagnostics: Mapped[dict] = mapped_column(JSON, default=dict)
    supporting_passages: Mapped[dict] = mapped_column(JSON, default=dict)
    contradictions: Mapped[list] = mapped_column(JSON, default=list)

    report_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ResearchSession", back_populates="report")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "owner_id": self.owner_id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "problem_landscape": self.problem_landscape or {},
            "target_audience": self.target_audience or {},
            "customer_pain_points": self.customer_pain_points or [],
            "competitor_analysis": self.competitor_analysis or [],
            "competitor_pricing": self.competitor_pricing or {},
            "market_trends": self.market_trends or [],
            "identified_opportunities": self.identified_opportunities or [],
            "opportunity_scores": self.opportunity_scores or {},
            "risks_and_limitations": self.risks_and_limitations or [],
            "actionable_recommendations": self.actionable_recommendations or [],
            "final_conclusion": self.final_conclusion,
            "sources": self.sources or [],
            "evidence_sufficiency": self.evidence_sufficiency,
            "used_live_search": self.used_live_search,
            "search_provider": self.search_provider,
            "search_mode": getattr(self, "search_mode", "curated_fallback") or "curated_fallback",
            "providers_diagnostics": getattr(self, "providers_diagnostics", {}) or {},
            "supporting_passages": getattr(self, "supporting_passages", {}) or {},
            "contradictions": getattr(self, "contradictions", []) or [],
            "created_at": safe_iso(self.created_at),
        }
