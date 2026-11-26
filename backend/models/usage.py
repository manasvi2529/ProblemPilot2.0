"""
Problem2Project AI — Usage Tracking, Quotas, and Token Blacklist Models.
Enforces multi-tenant resource boundaries, rate limits, and cost accounting.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base, safe_iso


class QuotaPolicy(Base):
    """Tier-specific quota configuration (free, pro, enterprise)."""
    __tablename__ = "quota_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tier: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # AI request quotas
    daily_ai_requests: Mapped[int] = mapped_column(Integer, default=50)
    monthly_ai_requests: Mapped[int] = mapped_column(Integer, default=1000)

    # Token quotas
    daily_tokens: Mapped[int] = mapped_column(Integer, default=100000)
    monthly_tokens: Mapped[int] = mapped_column(Integer, default=2000000)

    # Research session quotas
    daily_research_sessions: Mapped[int] = mapped_column(Integer, default=5)
    monthly_research_sessions: Mapped[int] = mapped_column(Integer, default=50)

    # Project and Execution quotas
    max_projects: Mapped[int] = mapped_column(Integer, default=10)
    max_concurrent_executions: Mapped[int] = mapped_column(Integer, default=1)

    # Deployment and Search
    daily_deployments: Mapped[int] = mapped_column(Integer, default=3)
    daily_search_calls: Mapped[int] = mapped_column(Integer, default=20)

    # Cost bound (USD)
    max_cost_usd: Mapped[float] = mapped_column(Float, default=5.0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tier": self.tier,
            "daily_ai_requests": self.daily_ai_requests,
            "monthly_ai_requests": self.monthly_ai_requests,
            "daily_tokens": self.daily_tokens,
            "monthly_tokens": self.monthly_tokens,
            "daily_research_sessions": self.daily_research_sessions,
            "monthly_research_sessions": self.monthly_research_sessions,
            "max_projects": self.max_projects,
            "max_concurrent_executions": self.max_concurrent_executions,
            "daily_deployments": self.daily_deployments,
            "daily_search_calls": self.daily_search_calls,
            "max_cost_usd": self.max_cost_usd,
            "updated_at": safe_iso(self.updated_at),
        }


class UserUsage(Base):
    """Aggregated usage metrics per user for daily and monthly periods."""
    __tablename__ = "user_usages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    period_type: Mapped[str] = mapped_column(String(20), default="daily")  # 'daily' | 'monthly'
    period_start: Mapped[str] = mapped_column(String(20), nullable=False)   # 'YYYY-MM-DD' or 'YYYY-MM'

    ai_requests_count: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    research_sessions_count: Mapped[int] = mapped_column(Integer, default=0)
    project_generation_requests: Mapped[int] = mapped_column(Integer, default=0)
    code_modifications_count: Mapped[int] = mapped_column(Integer, default=0)
    search_api_calls: Mapped[int] = mapped_column(Integer, default=0)
    active_preview_servers: Mapped[int] = mapped_column(Integer, default=0)
    deployments_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_user_usage_lookup", "user_id", "period_type", "period_start"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "period_type": self.period_type,
            "period_start": self.period_start,
            "ai_requests_count": self.ai_requests_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "research_sessions_count": self.research_sessions_count,
            "project_generation_requests": self.project_generation_requests,
            "code_modifications_count": self.code_modifications_count,
            "search_api_calls": self.search_api_calls,
            "active_preview_servers": self.active_preview_servers,
            "deployments_count": self.deployments_count,
            "execution_seconds": round(self.execution_seconds, 2),
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "updated_at": safe_iso(self.updated_at),
        }


class TokenBlacklist(Base):
    """Revoked session JWT tokens (e.g. on logout or security invalidation)."""
    __tablename__ = "token_blacklists"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jti": self.jti,
            "user_id": self.user_id,
            "revoked_at": safe_iso(self.revoked_at),
            "expires_at": safe_iso(self.expires_at),
        }
