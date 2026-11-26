"""
Problem2Project AI — Admin Governance, Usage Dashboard, and Audit Router.
Provides platform-wide visibility into multi-tenant consumption, active containers,
security events, user tiers, and cost management.
Protected by Administrator Role-Based Authorization.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.database import get_db
from backend.routers.auth import get_admin_user
from backend.models.user import User
from backend.models.project import Project
from backend.models.usage import QuotaPolicy, UserUsage
from backend.models.audit import AuditLog
from backend.services.quota_service import quota_service
from backend.services.execution_engine import execution_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class UpdateUserTierRequest(BaseModel):
    tier: Optional[str] = Field(None, description="free | pro | enterprise")
    role: Optional[str] = Field(None, description="user | admin")
    is_active: Optional[bool] = None


class UpdateTierPolicyRequest(BaseModel):
    daily_ai_requests: Optional[int] = None
    monthly_ai_requests: Optional[int] = None
    daily_tokens: Optional[int] = None
    monthly_tokens: Optional[int] = None
    daily_research_sessions: Optional[int] = None
    monthly_research_sessions: Optional[int] = None
    max_projects: Optional[int] = None
    max_concurrent_executions: Optional[int] = None
    daily_deployments: Optional[int] = None
    daily_search_calls: Optional[int] = None
    max_cost_usd: Optional[float] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/overview")
async def get_admin_overview(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Platform-level executive overview for administrators."""
    return await quota_service.get_platform_usage_summary(db)


@router.get("/users")
async def list_admin_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    role: Optional[str] = None,
    tier: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List registered users with their roles, tiers, and project counts."""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if tier:
        query = query.where(User.tier == tier)
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)

    res = await db.execute(query)
    users = res.scalars().all()

    user_list = []
    for u in users:
        proj_count = (await db.execute(select(func.count(Project.id)).where(Project.owner_id == u.id))).scalar_one()
        user_list.append({
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "tier": u.tier,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "total_projects": proj_count,
        })

    total_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    return {"total": total_count, "users": user_list}


@router.put("/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    body: UpdateUserTierRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Modify user role, tier, or activation status."""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_tier = user.tier
    old_role = user.role

    if body.tier:
        if body.tier.lower() not in ("free", "pro", "enterprise"):
            raise HTTPException(status_code=400, detail="Invalid tier. Allowed: free, pro, enterprise")
        user.tier = body.tier.lower()

    if body.role:
        if body.role.lower() not in ("user", "admin"):
            raise HTTPException(status_code=400, detail="Invalid role. Allowed: user, admin")
        user.role = body.role.lower()

    if body.is_active is not None:
        user.is_active = body.is_active

    db.add(AuditLog(
        user_id=admin.id,
        action="user.tier_modified",
        category="admin",
        description=f"Admin {admin.username} modified user {user.username}: tier={old_tier}->{user.tier}, role={old_role}->{user.role}",
        details={"target_user_id": user.id, "old_tier": old_tier, "new_tier": user.tier, "old_role": old_role, "new_role": user.role},
    ))
    await db.commit()
    await db.refresh(user)

    return {"success": True, "user": user.to_dict()}


@router.get("/quotas")
async def list_tier_quotas(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all configurable tier quota policies."""
    res = await db.execute(select(QuotaPolicy).order_by(QuotaPolicy.tier))
    policies = res.scalars().all()
    return {"policies": [p.to_dict() for p in policies]}


@router.put("/quotas/{tier}")
async def update_tier_quota(
    tier: str,
    body: UpdateTierPolicyRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Dynamically update quota thresholds for an account tier."""
    res = await db.execute(select(QuotaPolicy).where(QuotaPolicy.tier == tier.lower()))
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy for tier '{tier}' not found")

    for field, val in body.model_dump(exclude_unset=True).items():
        if val is not None:
            setattr(policy, field, val)

    policy.updated_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        user_id=admin.id,
        action="quota.policy_updated",
        category="admin",
        description=f"Admin {admin.username} updated quota policy for tier '{tier}'",
        details=body.model_dump(exclude_unset=True),
    ))
    await db.commit()
    await db.refresh(policy)

    return {"success": True, "policy": policy.to_dict()}


@router.get("/executions")
async def list_active_executions(
    admin: User = Depends(get_admin_user),
):
    """Inspect all currently running sandbox containers across all tenants."""
    active_procs = execution_engine.get_all_active_processes()
    return {
        "active_containers_count": len(active_procs),
        "containers": [
            {
                "project_id": p.project_id,
                "user_id": p.user_id,
                "port": p.port,
                "pid": p.pid,
                "entry_point": p.entry_point,
                "uptime_seconds": p.uptime_seconds,
                "status": p.status,
                "health_url": p.health_url,
                "started_at": p.started_at.isoformat() if p.started_at else None,
            }
            for p in active_procs
        ],
    }


@router.post("/executions/{project_id}/terminate")
async def force_terminate_execution(
    project_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Administrative force-termination of an active sandbox container."""
    with execution_engine._lock:
        proc_obj = execution_engine._processes.get(project_id)
        if not proc_obj or not proc_obj.is_alive():
            raise HTTPException(status_code=404, detail="No active running process found for this project.")
        target_user = proc_obj.user_id
        res = execution_engine.stop_project(project_id, target_user)

    db.add(AuditLog(
        user_id=admin.id,
        project_id=project_id,
        action="execution.force_terminated",
        category="admin",
        description=f"Admin {admin.username} forcibly terminated container for project {project_id}",
    ))
    await db.commit()

    return {"success": True, "result": res}


@router.get("/audit-logs")
async def get_admin_audit_logs(
    category: Optional[str] = None,
    action: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    user_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Full platform audit logs query with filtering and security diagnostics."""
    query = select(AuditLog)
    if category:
        query = query.where(AuditLog.category == category)
    if action:
        query = query.where(AuditLog.action == action)
    if status_filter:
        query = query.where(AuditLog.status == status_filter)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()

    total = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()

    return {
        "total": total,
        "logs": [log.to_dict() for log in logs],
    }


@router.get("/costs")
async def get_platform_costs_breakdown(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Detailed breakdown of estimated operating costs by provider and top users."""
    daily_key, monthly_key = quota_service.get_period_keys()

    stmt = select(UserUsage).where(
        UserUsage.period_type == "monthly",
        UserUsage.period_start == monthly_key,
    ).order_by(desc(UserUsage.estimated_cost_usd)).limit(10)

    res = await db.execute(stmt)
    top_usages = res.scalars().all()

    top_consumers = []
    for u in top_usages:
        user_obj = (await db.execute(select(User).where(User.id == u.user_id))).scalar_one_or_none()
        top_consumers.append({
            "user_id": u.user_id,
            "username": user_obj.username if user_obj else "unknown",
            "tier": user_obj.tier if user_obj else "unknown",
            "tokens": u.input_tokens + u.output_tokens,
            "cost_usd": round(u.estimated_cost_usd, 4),
            "ai_requests": u.ai_requests_count,
            "search_calls": u.search_api_calls,
        })

    platform_summary = await quota_service.get_platform_usage_summary(db)
    return {
        "period": monthly_key,
        "platform_totals": platform_summary["platform_monthly_totals"],
        "top_consuming_users": top_consumers,
    }
