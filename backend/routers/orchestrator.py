"""
ProblemPilot AI — Master Orchestrator Router
Unified endpoints powering the complete:
ONE PROMPT → LIVE RESEARCH → PROBLEM VALIDATION → OPPORTUNITY SELECTION →
PROJECT DESIGN → BUILD → TEST → GITHUB → DEPLOY
journey with live teaching, permissions, and cloud deployment.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from backend.database import get_db
from backend.routers.auth import get_user_from_token
from backend.models.user import User
from backend.models.project import Project, ProjectFile
from backend.services.agent_orchestrator import AgentOrchestrator
from backend.services.approval_engine import ApprovalEngine
from backend.services.ai_teacher import AITeacher

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])
orchestrator = AgentOrchestrator()
teacher = AITeacher()


# ── Request Schemas ──────────────────────────────────────────────────────────

class PromptJourneyRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000)

class RefineOpportunitiesRequest(BaseModel):
    session_id: Optional[str] = None
    feedback: str = Field(..., min_length=2, max_length=1000)
    history: Optional[List[Dict[str, str]]] = []
    current_opportunities: Optional[List[Dict[str, Any]]] = []

class BlueprintCustomizationRequest(BaseModel):
    tech_stack: Optional[Dict[str, Any]] = None
    custom_instructions: Optional[str] = None

class BuildWorkspaceRequest(BaseModel):
    force_build: Optional[bool] = False
    use_ai: Optional[bool] = True
    custom_instructions: Optional[str] = None

class ProjectChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[Dict[str, str]]] = []

class SuggestTechStackRequest(BaseModel):
    custom_requirements: Optional[str] = None
    apply: Optional[bool] = False

class ApplyTechStackRequest(BaseModel):
    tech_stack: Dict[str, Any]
    rearchitect: Optional[bool] = True
    custom_instructions: Optional[str] = None

class TestWorkspaceRequest(BaseModel):
    pass

class TeachRequest(BaseModel):
    topic: str
    context: Optional[str] = ""
    level: Optional[str] = "intermediate"

class GitHubSyncRequest(BaseModel):
    token: Optional[str] = None
    repository_name: Optional[str] = None
    private: Optional[bool] = True

class CloudDeployRequest(BaseModel):
    provider: Optional[str] = "vercel"
    provider_token: Optional[str] = None
    verify_url: Optional[str] = None


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/prompt")
async def start_prompt_journey(
    body: PromptJourneyRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute ONE PROMPT:
    Performs live multi-source research across communities and the web,
    validates user problems with Data Science metrics,
    and returns 3-5 ranked, evidence-backed opportunities.
    """
    try:
        result = await orchestrator.execute_prompt_journey(db, user, body.prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research journey failed: {str(e)}")


@router.post("/opportunities/refine")
async def refine_opportunities_endpoint(
    body: RefineOpportunitiesRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Conversational follow-up:
    Allows user to converse with AI, critique proposed opportunities,
    and receive fresh tailored opportunities matching their requested domain/stack/constraints.
    """
    try:
        return await orchestrator.refine_opportunities(
            db=db,
            user=user,
            session_id=body.session_id,
            feedback=body.feedback,
            history=body.history,
            current_opportunities=body.current_opportunities,
        )
    except Exception as e:
        logger.error(f"Opportunity refinement failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")


@router.post("/projects/{project_id}/blueprint")
async def generate_blueprint(
    project_id: str,
    body: Optional[BlueprintCustomizationRequest] = None,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Generate complete project blueprint tailored to the selected problem and optional custom tech stack."""
    try:
        tech_stack = body.tech_stack if body else None
        custom_instructions = body.custom_instructions if body else None
        return await orchestrator.generate_blueprint_stage(
            db=db,
            user=user,
            project_id=project_id,
            tech_stack=tech_stack,
            custom_instructions=custom_instructions,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/build")
async def build_project_workspace(
    project_id: str,
    body: Optional[BuildWorkspaceRequest] = None,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Generate actual full-stack source code into isolated project sandbox with AI or blueprint synthesizer."""
    try:
        force = body.force_build if body else False
        use_ai = body.use_ai if body and body.use_ai is not None else True
        custom_instructions = body.custom_instructions if body else None
        return await orchestrator.build_workspace_stage(
            db,
            user,
            project_id,
            force_build=force,
            use_ai=use_ai,
            custom_instructions=custom_instructions,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/test")
async def test_project_workspace(
    project_id: str,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Run automated verification tests in sandbox and return actual results."""
    try:
        return await orchestrator.test_workspace_stage(db, user, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/teach")
async def teach_concept(
    project_id: str,
    body: TeachRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """AI Teacher explanation grounded in actual project code, architecture, and interview prep."""
    if project_id == "global":
        explanation = await teacher.explain_concept(
            topic=body.topic,
            context=body.context or "General Software Architecture, System Design & Full-Stack Patterns",
            level=body.level or "intermediate",
            project_name="Full-Stack Application",
            files_context=None,
        )
        return {"explanation": explanation}

    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Load actual workspace files recursively if available
    workspace_dir = orchestrator.workspace_builder.get_workspace_dir(project.id, project.name)
    files_context = {}
    EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
    if workspace_dir.exists():
        for p in workspace_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(workspace_dir)
                parts = set(rel.parts)
                if parts & EXCLUDE_DIRS or any(part.startswith(".") for part in parts if part != ".gitignore"):
                    continue
                if p.name.startswith(".env") or p.suffix in (".pyc", ".log", ".pem", ".key"):
                    continue
                try:
                    files_context[rel.as_posix()] = p.read_text(encoding="utf-8", errors="ignore")[:600]
                except Exception:
                    pass

    context = body.context or f"Project '{project.name}': {project.description or ''}"
    explanation = await teacher.explain_concept(
        topic=body.topic,
        context=context,
        level=body.level or "intermediate",
        project_name=project.name,
        files_context=files_context,
    )
    if project.current_stage in ("discover", "architect", "build", "test"):
        project.current_stage = "teach"
        await db.commit()
    return {"explanation": explanation}


@router.post("/projects/{project_id}/github")
async def sync_github(
    project_id: str,
    body: GitHubSyncRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Scan for secrets, create repo, and push code to GitHub."""
    result = await orchestrator.push_github_stage(
        db=db,
        user=user,
        project_id=project_id,
        token=body.token,
        repo_name=body.repository_name,
        private=bool(body.private),
    )
    if not result.get("success") and not result.get("approval_required"):
        raise HTTPException(status_code=400, detail=result.get("error", "GitHub sync failed"))
    return result


@router.post("/projects/{project_id}/deploy")
async def deploy_cloud(
    project_id: str,
    body: CloudDeployRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Enforce deployment approval and execute authentic cloud deployment."""
    result = await orchestrator.deploy_cloud_stage(
        db=db,
        user=user,
        project_id=project_id,
        provider=body.provider or "vercel",
        provider_token=body.provider_token,
    )
    if body.verify_url:
        probe = await orchestrator.cloud_deployer.verify_remote_deployment(body.verify_url)
        result["verification"] = probe
    return result


@router.get("/projects/{project_id}/files")
async def get_workspace_files(
    project_id: str,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """List all source files from disk for the project workspace."""
    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    workspace_dir = orchestrator.workspace_builder.get_workspace_dir(project.id, project.name)
    files = []
    EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
    if workspace_dir.exists():
        for p in workspace_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(workspace_dir)
                parts = set(rel.parts)
                if parts & EXCLUDE_DIRS or any(part.startswith(".") for part in parts if part != ".gitignore"):
                    continue
                if p.name.startswith(".env") or p.suffix in (".pyc", ".log", ".pem", ".key"):
                    continue
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    ext = p.suffix.lstrip(".")
                    files.append({
                        "name": p.name,
                        "path": rel.as_posix(),
                        "extension": ext,
                        "size_bytes": p.stat().st_size,
                        "content": content,
                    })
                except Exception:
                    pass

    return {"files": files, "workspace_dir": str(workspace_dir)}


@router.post("/projects/{project_id}/chat")
async def chat_with_copilot(
    project_id: str,
    body: ProjectChatRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Interactive AI Copilot for project workspaces.
    Handles conversational questions, architecture trade-offs, tech stack recommendations,
    and guides AI code generation.
    """
    try:
        return await orchestrator.project_chat(
            db=db,
            user=user,
            project_id=project_id,
            message=body.message,
            history=body.history,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Project chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/suggest-tech-stack")
async def suggest_tech_stack_endpoint(
    project_id: str,
    body: Optional[SuggestTechStackRequest] = None,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Use AI to formulate an optimal, problem-tailored tech stack."""
    try:
        reqs = body.custom_requirements if body else None
        apply_flag = body.apply if body else False
        return await orchestrator.suggest_project_tech_stack(
            db=db,
            user=user,
            project_id=project_id,
            custom_requirements=reqs,
            apply=apply_flag,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Tech stack suggestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/apply-tech-stack")
async def apply_tech_stack_endpoint(
    project_id: str,
    body: ApplyTechStackRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Persist user or AI recommended tech stack into project."""
    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from backend.models.audit import AuditLog
    from datetime import datetime, timezone

    project.tech_stack = body.tech_stack
    project.updated_at = datetime.now(timezone.utc)

    # Re-architect blueprint dynamically if requested
    rearchitect_flag = body.rearchitect if body.rearchitect is not None else True
    if rearchitect_flag:
        try:
            new_blueprint = await orchestrator.project_architect.generate_blueprint(
                problem_title=project.name,
                problem_desc=project.description or "",
                tech_stack=body.tech_stack,
                custom_instructions=body.custom_instructions,
            )
            project.blueprint = new_blueprint
            project.current_stage = "architect"
        except Exception as e:
            logger.warning(f"Auto re-architecture on tech stack update failed: {e}")

    audit = AuditLog(
        user_id=user.id,
        project_id=project.id,
        action="update_tech_stack",
        category="project",
        description=f"Tech stack updated and blueprint re-architected for {project.name}",
        details={"tech_stack": body.tech_stack},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(project)
    return {
        "project": project.to_dict(),
        "blueprint": project.blueprint or {},
        "message": "Tech stack updated and blueprint re-architected successfully",
    }


