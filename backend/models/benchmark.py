"""
Benchmark and Evaluation models (Phase 1.8 Stage 3).
Tracks benchmark runs, test case scores, critical gate audits, and SHA-256 report digests.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Float, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base, safe_iso


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)

    suite_name: Mapped[str] = mapped_column(String(100), default="golden_v1")
    suite_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    
    # Status: running | completed | failed | cancelled
    status: Mapped[str] = mapped_column(String(30), default="running")
    overall_status: Mapped[str] = mapped_column(String(30), default="PENDING")  # PASSED | FAILED_GATE | DEGRADED | PENDING

    # Aggregated metrics
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0)

    average_score: Mapped[float] = mapped_column(Float, default=0.0)
    research_avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    blueprint_avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    app_avg_score: Mapped[float] = mapped_column(Float, default=0.0)

    passed_all_critical_gates: Mapped[bool] = mapped_column(Boolean, default=False)
    sha256_report_digest: Mapped[str] = mapped_column(String(64), nullable=True)

    # Detailed report data stored as JSON
    report_data: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User")
    project = relationship("Project")
    case_results = relationship("EvaluationResult", back_populates="benchmark_run", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "project_id": self.project_id,
            "suite_name": self.suite_name,
            "suite_version": self.suite_version,
            "status": self.status,
            "overall_status": self.overall_status,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "average_score": self.average_score,
            "research_avg_score": self.research_avg_score,
            "blueprint_avg_score": self.blueprint_avg_score,
            "app_avg_score": self.app_avg_score,
            "passed_all_critical_gates": self.passed_all_critical_gates,
            "sha256_report_digest": self.sha256_report_digest,
            "report_data": self.report_data or {},
            "created_at": safe_iso(self.created_at),
            "completed_at": safe_iso(self.completed_at),
        }


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    benchmark_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("benchmark_runs.id"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(100), nullable=False)
    case_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    case_digest: Mapped[str] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="PENDING")  # PASSED | FAILED_GATE | DEGRADED
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    research_score: Mapped[float] = mapped_column(Float, default=0.0)
    blueprint_score: Mapped[float] = mapped_column(Float, default=0.0)
    app_score: Mapped[float] = mapped_column(Float, default=0.0)

    passed_all_gates: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    gate_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    research_result: Mapped[dict] = mapped_column(JSON, default=dict)
    blueprint_result: Mapped[dict] = mapped_column(JSON, default=dict)
    app_result: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    benchmark_run = relationship("BenchmarkRun", back_populates="case_results")

    def to_dict(self):
        return {
            "id": self.id,
            "benchmark_run_id": self.benchmark_run_id,
            "case_id": self.case_id,
            "case_version": self.case_version,
            "case_digest": self.case_digest,
            "status": self.status,
            "overall_score": self.overall_score,
            "research_score": self.research_score,
            "blueprint_score": self.blueprint_score,
            "app_score": self.app_score,
            "passed_all_gates": self.passed_all_gates,
            "duration_seconds": self.duration_seconds,
            "gate_summary": self.gate_summary or {},
            "research_result": self.research_result or {},
            "blueprint_result": self.blueprint_result or {},
            "app_result": self.app_result or {},
            "created_at": safe_iso(self.created_at),
        }
