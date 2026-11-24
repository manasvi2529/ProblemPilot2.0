"""
ProblemPilot AI — Iterative Editor Router
Endpoints for natural-language change planning, user approval, safe code modification,
snapshot history, and rollback.
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.routers.auth import get_user_from_token
from backend.models.user import User
from backend.models.project import Project
from backend.services.workspace_builder import WorkspaceBuilder
from backend.services.iterative_engine import change_planner, code_modification_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/editor", tags=["editor"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class PlanChangeRequest(BaseModel):
    instruction: str = Field(..., min_length=2, max_length=2000)
    conversation_history: Optional[List[Dict[str, str]]] = None


class ApplyChangeRequest(BaseModel):
    plan_id: str
    approved: bool = True
    plan: Optional[Dict[str, Any]] = None
    custom_adjustments: Optional[str] = None


class RollbackRequest(BaseModel):
    version: Optional[int] = None


# Cache pending plans in-memory for review
_pending_plans: Dict[str, Dict[str, Any]] = {}


async def _get_authorized_project(
    project_id: str,
    user: User,
    db: AsyncSession,
) -> Project:
    """Verify project exists and belongs to the authenticated user."""
    stmt = select(Project).where(Project.id == project_id, Project.owner_id == user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to access it.",
        )
    return project


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/plan")
async def plan_project_change(
    project_id: str,
    payload: PlanChangeRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Formulate a structured change plan from natural-language instructions.
    Returns proposed patches, affected files, risks, and validation plan for user approval.
    """
    project = await _get_authorized_project(project_id, user, db)
    workspace_dir = WorkspaceBuilder.get_workspace_dir(project.id, project.name)

    if not workspace_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project workspace has not been generated yet. Build the project first.",
        )

    plan = await change_planner.plan_changes(
        project_id=project.id,
        instruction=payload.instruction,
        blueprint=project.blueprint or {},
        workspace_dir=workspace_dir,
        history=payload.conversation_history,
    )

    _pending_plans[plan["plan_id"]] = plan
    return plan


@router.post("/projects/{project_id}/apply")
async def apply_project_change(
    project_id: str,
    payload: ApplyChangeRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply an approved change plan or reject it.
    If approved is False, zero modifications are applied.
    If approved is True, creates snapshot, executes patches, validates syntax, and reloads preview.
    """
    project = await _get_authorized_project(project_id, user, db)
    workspace_dir = WorkspaceBuilder.get_workspace_dir(project.id, project.name)

    # 1. Handle user rejection
    if not payload.approved:
        if payload.plan_id in _pending_plans:
            _pending_plans[payload.plan_id]["status"] = "rejected"
        return {
            "success": True,
            "status": "rejected",
            "message": "Change plan was rejected by the user. No files were modified.",
            "files_modified": [],
            "files_created": [],
        }

    # 2. Retrieve plan
    plan = payload.plan or _pending_plans.get(payload.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Change plan {payload.plan_id} not found or expired. Please re-plan your request.",
        )

    # 3. Apply changes via CodeModificationEngine
    result = await code_modification_engine.apply_plan(
        project_id=project.id,
        user_id=user.id,
        plan=plan,
        workspace_dir=workspace_dir,
        db=db,
    )

    if not result.get("success"):
        return result

    if payload.plan_id in _pending_plans:
        _pending_plans[payload.plan_id]["status"] = "applied"

    return result


@router.get("/projects/{project_id}/history")
async def get_project_change_history(
    project_id: str,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve snapshot history and audit trail of previous modifications.
    """
    project = await _get_authorized_project(project_id, user, db)
    workspace_dir = WorkspaceBuilder.get_workspace_dir(project.id, project.name)

    history = code_modification_engine.get_history(workspace_dir)
    return {
        "project_id": project.id,
        "total_versions": len(history),
        "history": history,
    }


@router.post("/projects/{project_id}/rollback")
async def rollback_project_change(
    project_id: str,
    payload: RollbackRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Roll back workspace files to a specific snapshot version or the immediately preceding snapshot.
    """
    project = await _get_authorized_project(project_id, user, db)
    workspace_dir = WorkspaceBuilder.get_workspace_dir(project.id, project.name)

    return await code_modification_engine.rollback(
        project_id=project.id,
        user_id=user.id,
        workspace_dir=workspace_dir,
        target_version=payload.version,
        db=db,
    )

