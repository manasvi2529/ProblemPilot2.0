"""
Problem2Project AI — Centralized Quota & Usage Management Service.
Enforces multi-tenant consumption boundaries, resource controls, and provider cost tracking.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from backend.models.user import User
from backend.models.usage import QuotaPolicy, UserUsage
from backend.models.audit import AuditLog

logger = logging.getLogger(__name__)

# Standard AI & External Provider Unit Cost Benchmarks (per token / per operation)
PROVIDER_COST_RATES = {
    "openrouter_llama": {"input_per_m": 0.12, "output_per_m": 0.30},
    "gemini_flash": {"input_per_m": 0.10, "output_per_m": 0.40},
    "anthropic_sonnet": {"input_per_m": 3.00, "output_per_m": 15.00},
    "default_ai": {"input_per_m": 0.15, "output_per_m": 0.50},
    "search_query": 0.005,           # $0.005 per Serper/Brave query
    "execution_per_second": 0.00002, # Container compute rate (~$0.072/hr)
}

# Fallback default tier limits if database row not loaded
DEFAULT_TIER_LIMITS = {
    "free": {
        "daily_ai_requests": 50,
        "monthly_ai_requests": 1000,
        "daily_tokens": 100000,
        "monthly_tokens": 2000000,
        "daily_research_sessions": 5,
        "monthly_research_sessions": 50,
        "max_projects": 10,
        "max_concurrent_executions": 1,
        "daily_deployments": 3,
        "daily_search_calls": 20,
        "max_cost_usd": 5.0,
    },
    "pro": {
        "daily_ai_requests": 500,
        "monthly_ai_requests": 10000,
        "daily_tokens": 1000000,
        "monthly_tokens": 20000000,
        "daily_research_sessions": 50,
        "monthly_research_sessions": 500,
        "max_projects": 50,
        "max_concurrent_executions": 3,
        "daily_deployments": 20,
        "daily_search_calls": 200,
        "max_cost_usd": 50.0,
    },
    "enterprise": {
        "daily_ai_requests": 5000,
        "monthly_ai_requests": 100000,
        "daily_tokens": 10000000,
        "monthly_tokens": 200000000,
        "daily_research_sessions": 500,
        "monthly_research_sessions": 5000,
        "max_projects": 500,
        "max_concurrent_executions": 10,
        "daily_deployments": 100,
        "daily_search_calls": 2000,
        "max_cost_usd": 500.0,
    },
}


class QuotaService:
    """Unified service for quota policy retrieval, enforcement, and usage recording."""

    @classmethod
    def get_period_keys(cls) -> Tuple[str, str]:
        """Return ISO period strings for today ('YYYY-MM-DD') and this month ('YYYY-MM')."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")

    @classmethod
    def calculate_estimated_cost(
        cls,
        tokens_in: int = 0,
        tokens_out: int = 0,
        search_calls: int = 0,
        execution_seconds: float = 0.0,
        model_name: str = "default_ai",
    ) -> float:
        """Estimate operating cost in USD for given operations."""
        rates = PROVIDER_COST_RATES.get(model_name, PROVIDER_COST_RATES["default_ai"])
        ai_cost = (tokens_in / 1_000_000) * rates["input_per_m"] + (tokens_out / 1_000_000) * rates["output_per_m"]
        search_cost = search_calls * PROVIDER_COST_RATES["search_query"]
        compute_cost = execution_seconds * PROVIDER_COST_RATES["execution_per_second"]
        return round(ai_cost + search_cost + compute_cost, 6)

    @classmethod
    async def get_tier_policy(cls, db: AsyncSession, tier: str) -> Dict[str, Any]:
        """Retrieve quota policy from DB or fall back to default definition."""
        tier_clean = (tier or "free").lower()
        res = await db.execute(select(QuotaPolicy).where(QuotaPolicy.tier == tier_clean))
        policy_obj = res.scalar_one_or_none()
        if policy_obj:
            return policy_obj.to_dict()
        return DEFAULT_TIER_LIMITS.get(tier_clean, DEFAULT_TIER_LIMITS["free"])

    @classmethod
    async def get_or_create_usage(
        cls,
        db: AsyncSession,
        user_id: str,
        period_type: str,
        period_start: str,
    ) -> UserUsage:
        """Retrieve or initialize a UserUsage record for a specific user and period."""
        res = await db.execute(
            select(UserUsage).where(
                UserUsage.user_id == user_id,
                UserUsage.period_type == period_type,
                UserUsage.period_start == period_start,
            )
        )
        usage = res.scalar_one_or_none()
        if not usage:
            usage = UserUsage(
                user_id=user_id,
                period_type=period_type,
                period_start=period_start,
            )
            db.add(usage)
            await db.flush()
        return usage

    @classmethod
    async def check_quota(
        cls,
        db: AsyncSession,
        user: User,
        action_type: str,
        units: int = 1,
    ) -> None:
        """
        Check whether an intended operation is permitted under the user's active tier policy.
        Raises HTTP 429 with structured details if limit is exceeded.
        Admins bypass limits.
        """
        if getattr(user, "is_admin", False) or getattr(user, "role", "user") == "admin":
            return

        tier = getattr(user, "tier", "free") or "free"
        policy = await cls.get_tier_policy(db, tier)
        daily_key, monthly_key = cls.get_period_keys()

        daily_usage = await cls.get_or_create_usage(db, user.id, "daily", daily_key)
        monthly_usage = await cls.get_or_create_usage(db, user.id, "monthly", monthly_key)

        # Mapping action_type to quota limits and usage fields
        ACTION_MAP = {
            "ai_request": ("daily_ai_requests", daily_usage.ai_requests_count, "monthly_ai_requests", monthly_usage.ai_requests_count),
            "research_session": ("daily_research_sessions", daily_usage.research_sessions_count, "monthly_research_sessions", monthly_usage.research_sessions_count),
            "search_call": ("daily_search_calls", daily_usage.search_api_calls, None, 0),
            "deployment": ("daily_deployments", daily_usage.deployments_count, None, 0),
        }

        if action_type in ACTION_MAP:
            d_limit_name, d_used, m_limit_name, m_used = ACTION_MAP[action_type]
            # 1. Check daily limit
            d_limit = policy.get(d_limit_name, 999999)
            if d_used + units > d_limit:
                now = datetime.now(timezone.utc)
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                reset_seconds = int((tomorrow - now).total_seconds())

                # Record security/audit event
                db.add(AuditLog(
                    user_id=user.id,
                    action="quota.exhausted",
                    category="usage",
                    description=f"User exceeded daily quota for {action_type} (Limit: {d_limit}, Current: {d_used})",
                    status="failure",
                    details={"action": action_type, "limit": d_limit, "used": d_used, "tier": tier},
                ))
                await db.commit()

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "quota_exceeded",
                        "action_type": action_type,
                        "period": "daily",
                        "limit": d_limit,
                        "used": d_used,
                        "remaining": max(0, d_limit - d_used),
                        "reset_seconds": reset_seconds,
                        "tier": tier,
                        "message": f"Daily {action_type.replace('_', ' ')} quota of {d_limit} exceeded for tier '{tier}'. Resets in {reset_seconds // 3600}h {(reset_seconds % 3600) // 60}m.",
                    },
                    headers={"Retry-After": str(reset_seconds)},
                )

            # 2. Check monthly limit if applicable
            if m_limit_name:
                m_limit = policy.get(m_limit_name, 999999)
                if m_used + units > m_limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "quota_exceeded",
                            "action_type": action_type,
                            "period": "monthly",
                            "limit": m_limit,
                            "used": m_used,
                            "remaining": max(0, m_limit - m_used),
                            "tier": tier,
                            "message": f"Monthly {action_type.replace('_', ' ')} quota of {m_limit} exceeded for tier '{tier}'. Please upgrade to continue.",
                        },
                    )

        # Check concurrent execution limit
        if action_type == "start_preview":
            from backend.services.execution_engine import execution_engine
            running_procs = execution_engine.get_active_processes_for_user(user.id)
            max_concurrent = policy.get("max_concurrent_executions", 1)
            if len(running_procs) >= max_concurrent:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "concurrent_execution_limit",
                        "limit": max_concurrent,
                        "active": len(running_procs),
                        "tier": tier,
                        "message": f"Concurrent sandbox execution limit of {max_concurrent} reached for tier '{tier}'. Stop an existing running application to launch another.",
                    },
                )

    @classmethod
    async def record_usage(
        cls,
        db: AsyncSession,
        user: User,
        action_type: str,
        units: int = 1,
        tokens_in: int = 0,
        tokens_out: int = 0,
        search_calls: int = 0,
        execution_seconds: float = 0.0,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Atomically record consumption event across daily and monthly usage records."""
        daily_key, monthly_key = cls.get_period_keys()
        daily_usage = await cls.get_or_create_usage(db, user.id, "daily", daily_key)
        monthly_usage = await cls.get_or_create_usage(db, user.id, "monthly", monthly_key)

        calculated_cost = cost_usd if cost_usd is not None else cls.calculate_estimated_cost(
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            search_calls=search_calls,
            execution_seconds=execution_seconds,
        )

        for record in (daily_usage, monthly_usage):
            if action_type in ("ai_request", "copilot_chat", "generate_blueprint"):
                record.ai_requests_count += units
            elif action_type == "research_session":
                record.research_sessions_count += units
            elif action_type == "project_generation":
                record.project_generation_requests += units
            elif action_type == "code_modification":
                record.code_modifications_count += units
            elif action_type == "deployment":
                record.deployments_count += units

            record.input_tokens += tokens_in
            record.output_tokens += tokens_out
            record.search_api_calls += search_calls
            record.execution_seconds += execution_seconds
            record.estimated_cost_usd += calculated_cost
            record.updated_at = datetime.now(timezone.utc)

        await db.commit()

    @classmethod
    async def get_user_usage_summary(cls, db: AsyncSession, user: User) -> Dict[str, Any]:
        """Compile comprehensive usage report with limits, consumption, and remaining balances."""
        tier = getattr(user, "tier", "free") or "free"
        policy = await cls.get_tier_policy(db, tier)
        daily_key, monthly_key = cls.get_period_keys()

        daily_usage = await cls.get_or_create_usage(db, user.id, "daily", daily_key)
        monthly_usage = await cls.get_or_create_usage(db, user.id, "monthly", monthly_key)

        from backend.services.execution_engine import execution_engine
        running_procs = execution_engine.get_active_processes_for_user(user.id)

        return {
            "user_id": user.id,
            "username": user.username,
            "tier": tier,
            "is_admin": getattr(user, "is_admin", False),
            "limits": policy,
            "daily_usage": daily_usage.to_dict(),
            "monthly_usage": monthly_usage.to_dict(),
            "active_executions": len(running_procs),
            "remaining": {
                "daily_ai_requests": max(0, policy.get("daily_ai_requests", 0) - daily_usage.ai_requests_count),
                "monthly_ai_requests": max(0, policy.get("monthly_ai_requests", 0) - monthly_usage.ai_requests_count),
                "daily_research_sessions": max(0, policy.get("daily_research_sessions", 0) - daily_usage.research_sessions_count),
                "daily_search_calls": max(0, policy.get("daily_search_calls", 0) - daily_usage.search_api_calls),
                "concurrent_executions": max(0, policy.get("max_concurrent_executions", 1) - len(running_procs)),
            },
        }

    @classmethod
    async def get_platform_usage_summary(cls, db: AsyncSession) -> Dict[str, Any]:
        """Admin dashboard: platform-wide resource consumption, cost breakdown, and top consumers."""
        total_users = (await db.execute(select(func.count(User.id)))).scalar_one()

        daily_key, monthly_key = cls.get_period_keys()
        
        # Monthly platform totals
        stmt = select(
            func.sum(UserUsage.ai_requests_count),
            func.sum(UserUsage.input_tokens),
            func.sum(UserUsage.output_tokens),
            func.sum(UserUsage.research_sessions_count),
            func.sum(UserUsage.search_api_calls),
            func.sum(UserUsage.estimated_cost_usd),
            func.sum(UserUsage.execution_seconds),
        ).where(UserUsage.period_type == "monthly", UserUsage.period_start == monthly_key)

        res = await db.execute(stmt)
        row = res.fetchone()

        from backend.services.execution_engine import execution_engine
        active_processes = execution_engine.get_all_active_processes()

        return {
            "period": monthly_key,
            "total_registered_users": total_users,
            "active_sandbox_containers": len(active_processes),
            "platform_monthly_totals": {
                "ai_requests": row[0] or 0,
                "input_tokens": row[1] or 0,
                "output_tokens": row[2] or 0,
                "total_tokens": (row[1] or 0) + (row[2] or 0),
                "research_sessions": row[3] or 0,
                "search_api_calls": row[4] or 0,
                "total_cost_usd": round(row[5] or 0.0, 4),
                "execution_hours": round((row[6] or 0.0) / 3600, 2),
            },
            "active_processes": [
                {
                    "project_id": p.project_id,
                    "user_id": p.user_id,
                    "port": p.port,
                    "pid": p.pid,
                    "uptime_seconds": p.uptime_seconds,
                    "status": p.status,
                }
                for p in active_processes
            ],
        }


quota_service = QuotaService()
