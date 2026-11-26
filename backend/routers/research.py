"""
Research router — live problem discovery and evidence collection.
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.routers.auth import get_user_from_token, get_optional_user
from backend.models.user import User
from backend.models.research import ResearchSession, ResearchSource, ProblemCandidate, ResearchReport
from backend.models.project import Project
from backend.models.audit import AuditLog
from backend.services.research_service import (
    perform_web_search, fetch_page_content, analyze_with_ai,
    build_analysis_prompt, build_scoring_weights,
)
from backend.services.live_research_engine import live_research_engine
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    domain: str = ""
    target_users: str = ""
    geography: str = ""
    constraints: str = ""

class RefineRequest(BaseModel):
    additional_query: str = Field(..., min_length=3)


# ── Background Research Task ────────────────────────────────────────────────

async def run_research_pipeline(session_id: str, query: str):
    """Execute the full research pipeline in the background."""
    from backend.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Get session
        result = await db.execute(
            select(ResearchSession).where(ResearchSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return

        try:
            # Step 1: Web search
            session.status = "searching"
            await db.commit()

            search_query = query
            if session.domain:
                search_query = f"{query} {session.domain}"
            if session.geography:
                search_query += f" {session.geography}"

            search_results, provider, is_live = await perform_web_search(search_query)
            session.used_live_search = is_live
            session.search_provider = provider

            if not search_results and not is_live:
                session.status = "failed"
                session.error_message = (
                    f"Search provider '{provider}' is not configured or returned no results. "
                    f"Please configure SEARCH_API_KEY in your .env file. "
                    f"Supported providers: google_custom, serper, brave."
                )
                await db.commit()
                return

            # Step 2: Fetch page content for top results
            session.status = "analyzing"
            await db.commit()

            sources_data = []
            for sr in search_results[:8]:  # Limit to 8 pages
                page = await fetch_page_content(sr["url"])
                source = ResearchSource(
                    session_id=session_id,
                    url=sr["url"],
                    title=sr.get("title", page.get("title", "")),
                    publisher=sr.get("publisher", ""),
                    snippet=sr.get("snippet", ""),
                    full_text=page.get("text", "")[:10000],
                    publication_date=page.get("publication_date"),
                    source_type="web",
                    reliability="unassessed",
                )
                db.add(source)
                sources_data.append({
                    "url": sr["url"],
                    "title": sr.get("title", ""),
                    "snippet": sr.get("snippet", ""),
                    "text": page.get("text", "")[:3000],
                })

            await db.commit()

            # Step 3: AI analysis to extract problems
            if settings.ai_configured:
                prompt = build_analysis_prompt(query, sources_data)
                ai_response = await analyze_with_ai(prompt)

                if ai_response:
                    # Parse the JSON response
                    try:
                        # Clean up potential markdown wrapping
                        cleaned = ai_response.strip()
                        if cleaned.startswith("```"):
                            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
                            cleaned = cleaned.rsplit("```", 1)[0] if "```" in cleaned else cleaned
                            cleaned = cleaned.strip()

                        problems = json.loads(cleaned)
                        weights = build_scoring_weights()

                        # Get source IDs
                        src_result = await db.execute(
                            select(ResearchSource.id).where(ResearchSource.session_id == session_id)
                        )
                        source_ids = [r[0] for r in src_result.all()]

                        for i, p in enumerate(problems):
                            scores = p.get("scores", {})
                            # Calculate weighted overall score
                            overall = 0.0
                            total_weight = 0.0
                            for dim, weight in weights.items():
                                if dim in scores and isinstance(scores[dim], dict):
                                    overall += scores[dim].get("score", 0) * weight
                                    total_weight += weight
                            if total_weight > 0:
                                overall = overall / total_weight

                            problem = ProblemCandidate(
                                session_id=session_id,
                                title=p.get("title", f"Problem {i+1}"),
                                description=p.get("description", ""),
                                affected_users=p.get("affected_users", ""),
                                existing_solutions=p.get("existing_solutions", ""),
                                solution_gaps=p.get("solution_gaps", ""),
                                evidence_summary=p.get("evidence_summary", ""),
                                claim_type=p.get("claim_type", "inference"),
                                scores=scores,
                                overall_score=round(overall, 2),
                                score_weights=weights,
                                evidence_gaps=p.get("evidence_gaps", []),
                                contradictions=p.get("contradictions", []),
                                source_ids=source_ids,
                                rank=i + 1,
                                status="evaluated",
                            )
                            db.add(problem)

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse AI response: {e}")
                        # Create a single problem from raw AI response
                        problem = ProblemCandidate(
                            session_id=session_id,
                            title="AI analysis available (parsing failed)",
                            description=ai_response[:2000],
                            claim_type="inference",
                            status="identified",
                            rank=1,
                        )
                        db.add(problem)
            else:
                # No AI configured — still save sources, note limitation
                session.error_message = (
                    "AI provider not configured. Sources were collected but problem extraction "
                    "requires a configured AI provider (set GOOGLE_API_KEY or ANTHROPIC_API_KEY)."
                )

            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            logger.error(f"Research pipeline failed: {e}", exc_info=True)
            session.status = "failed"
            session.error_message = str(e)
            await db.commit()


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/sessions")
async def create_research_session(
    body: ResearchRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Start a new research session with live web search."""
    session = ResearchSession(
        owner_id=user.id,
        query=body.query,
        domain=body.domain,
        target_users=body.target_users,
        geography=body.geography,
        constraints=body.constraints,
        status="pending",
    )
    db.add(session)

    log = AuditLog(
        user_id=user.id, action="start_research", category="research",
        description=f"Research started: {body.query}",
    )
    db.add(log)
    await db.commit()
    await db.refresh(session)

    # Run research pipeline in background
    background_tasks.add_task(run_research_pipeline, session.id, body.query)

    return {
        "session": session.to_dict(),
        "message": "Research session started. Check status with GET /api/research/sessions/{id}",
        "search_configured": settings.search_configured,
        "ai_configured": settings.ai_configured,
    }


@router.get("/sessions")
async def list_research_sessions(
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """List research sessions with support for demo / public and authenticated modes."""
    query = (
        select(ResearchSession)
        .options(selectinload(ResearchSession.sources), selectinload(ResearchSession.problems))
    )
    if user:
        query = query.where((ResearchSession.owner_id == user.id) | (ResearchSession.owner_id == None))
    query = query.order_by(ResearchSession.created_at.desc()).limit(25)
    result = await db.execute(query)
    sessions = result.scalars().all()
    return {"sessions": [s.to_dict() for s in sessions]}


@router.get("/sessions/{session_id}")
async def get_research_session(
    session_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a research session with its sources and discovered problems."""
    result = await db.execute(
        select(ResearchSession)
        .where(ResearchSession.id == session_id)
        .options(selectinload(ResearchSession.sources), selectinload(ResearchSession.problems))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    return {
        "session": session.to_dict(),
        "sources": [s.to_dict() for s in (session.sources or [])],
        "problems": sorted(
            [p.to_dict() for p in (session.problems or [])],
            key=lambda x: x.get("overall_score", 0),
            reverse=True,
        ),
    }


@router.get("/sessions/{session_id}/problems")
async def get_session_problems(
    session_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all problem candidates discovered in a specific session."""
    sess_check = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    if not sess_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Research session not found")

    result = await db.execute(
        select(ProblemCandidate)
        .where(ProblemCandidate.session_id == session_id)
        .order_by(ProblemCandidate.overall_score.desc())
    )
    problems = result.scalars().all()
    return {"problems": [p.to_dict() for p in problems]}


@router.get("/integration-status")
async def research_integration_status():
    """Check which research integrations are configured with masked key diagnostics."""
    diagnostics = settings.get_search_provider_diagnostics()
    return {
        "search": {
            "configured": settings.search_configured,
            "provider": settings.SEARCH_PROVIDER,
            "canonical_search_mode": "live" if settings.search_configured else "curated_fallback",
            "message": (
                f"Ready for live search ({settings.SEARCH_PROVIDER})" if settings.search_configured
                else "No search API credentials found in .env. Operating in transparent curated fallback mode."
            ),
            "diagnostics": diagnostics,
        },
        "ai": {
            "configured": settings.ai_configured,
            "provider": settings.AI_PROVIDER,
            "message": (
                "AI analysis ready" if settings.ai_configured
                else f"Not configured. Set OPENROUTER_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY in .env"
            ),
        },
    }


# ── Phase 1.5: Live Research & Opportunity Validation Endpoints ───────────────

class LiveResearchValidateRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    domain: Optional[str] = ""
    geography: Optional[str] = ""
    target_users: Optional[str] = ""
    constraints: Optional[str] = ""
    sync: Optional[bool] = False


class ConvertReportRequest(BaseModel):
    opportunity_index: int = 0
    title: Optional[str] = None
    description: Optional[str] = None
    approved: bool = Field(True, description="Explicit user confirmation to convert research opportunity into a project.")
    approved_blueprint_hash: Optional[str] = Field(None, description="Cryptographic SHA-256 hash of the previewed blueprint.")
    approve_experimental_hypotheses: bool = Field(False, description="Explicit user confirmation to approve unverified experimental hypotheses.")


async def execute_live_research_pipeline(
    session_id: str,
    user_id: str,
    query: str,
    domain: str = "",
    target_users: str = "",
    geography: str = "",
    constraints: str = "",
):
    """
    Background asynchronous execution of the full live research pipeline.
    Persists real-time progress at each step for status polling and resilience.
    """
    from backend.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
        session = res.scalar_one_or_none()
        if not session or session.status == "cancelled":
            return

        try:
            # ── Step 1: Query Formulation & Live Evidence Retrieval (20%) ──
            session.status = "searching"
            session.progress_pct = 20
            session.current_step = "searching"
            session.step_message = "Searching live web and community discussion forums..."
            await db.commit()

            evidence = await live_research_engine.gather_evidence(
                query=query,
                domain=domain,
                geography=geography,
                target_users=target_users,
            )

            # Check for mid-flight cancellation
            res_chk = await db.execute(select(ResearchSession.status).where(ResearchSession.id == session_id))
            if res_chk.scalar_one_or_none() == "cancelled":
                return

            sources_data = evidence.get("sources", [])
            used_live = evidence.get("used_live_search", False)
            provider_name = evidence.get("search_provider", "")
            search_mode = evidence.get("search_mode", "curated_fallback")

            # ── Step 2: Content Extraction & Fact Classification (45%) ──
            session.status = "extracting"
            session.progress_pct = 45
            session.current_step = "extracting"
            session.step_message = f"Retrieved {len(sources_data)} sources. Extracting evidence, authors, and dates..."
            session.used_live_search = used_live
            session.search_provider = provider_name
            session.search_mode = search_mode
            session.providers_attempted = evidence.get("providers_attempted", [])
            session.providers_diagnostics = evidence.get("providers_diagnostics", {})
            session.failover_occurred = evidence.get("failover_occurred", False)
            await db.commit()

            source_records = []
            for s in sources_data:
                src = ResearchSource(
                    session_id=session.id,
                    url=s.get("url", ""),
                    title=s.get("title", ""),
                    publisher=s.get("publisher", ""),
                    snippet=s.get("snippet", ""),
                    raw_snippet=s.get("raw_snippet", s.get("snippet", "")),
                    full_text=s.get("full_text", "")[:4000],
                    publication_date=s.get("publication_date"),
                    source_type=s.get("source_type", "web"),
                    reliability=s.get("reliability", "medium"),
                    provider=s.get("provider", "unknown"),
                    is_live=s.get("is_live", False),
                    content_extracted=s.get("content_extracted", False),
                    retrieval_status=s.get("retrieval_status", "success"),
                    extraction_error=s.get("extraction_error"),
                    supporting_passage=s.get("supporting_passage", ""),
                )
                db.add(src)
                source_records.append(src)
            await db.commit()

            # ── Step 3: 6 Core Analyses & Competitor Analysis (70%) ────────
            session.status = "analyzing"
            session.progress_pct = 70
            session.current_step = "analyzing"
            session.step_message = "Analyzing problem landscape, target audience, and competitor pricing..."
            await db.commit()

            report_dict = await live_research_engine.analyze_and_generate_report(
                query=query,
                domain=domain,
                geography=geography,
                target_users=target_users,
                sources=sources_data,
                used_live_search=used_live,
                search_provider=provider_name,
                search_mode=search_mode,
            )

            # ── Step 4: 6-Dimension Opportunity Scoring (85%) ───────────────
            session.status = "scoring"
            session.progress_pct = 85
            session.current_step = "scoring"
            session.step_message = "Calculating transparent 6-dimension viability scores..."
            await db.commit()

            # ── Step 5: Synthesize 13-Section Report & Persist (100%) ──────
            report_record = ResearchReport(
                session_id=session.id,
                owner_id=user_id,
                title=report_dict.get("title", f"Report: {query}"),
                executive_summary=report_dict.get("executive_summary", ""),
                problem_landscape=report_dict.get("problem_landscape", {}),
                target_audience=report_dict.get("target_audience", {}),
                customer_pain_points=report_dict.get("customer_pain_points", []),
                competitor_analysis=report_dict.get("competitor_analysis", []),
                competitor_pricing=report_dict.get("competitor_pricing", {}),
                market_trends=report_dict.get("market_trends", []),
                identified_opportunities=report_dict.get("identified_opportunities", []),
                opportunity_scores=report_dict.get("opportunity_scores", {}),
                risks_and_limitations=report_dict.get("risks_and_limitations", []),
                actionable_recommendations=report_dict.get("actionable_recommendations", []),
                final_conclusion=report_dict.get("final_conclusion", ""),
                sources=report_dict.get("sources", []),
                evidence_sufficiency=report_dict.get("evidence_sufficiency", "moderate"),
                used_live_search=used_live,
                search_provider=provider_name,
                search_mode=report_dict.get("search_mode", search_mode),
                providers_diagnostics=evidence.get("providers_diagnostics", {}),
                supporting_passages=report_dict.get("supporting_passages", {}),
                contradictions=report_dict.get("contradictions", []),
                report_data=report_dict,
            )
            db.add(report_record)

            source_ids = [s.id for s in source_records]
            for i, opp in enumerate(report_dict.get("identified_opportunities", []), 1):
                scores = report_dict.get("opportunity_scores", {})
                cand = ProblemCandidate(
                    session_id=session.id,
                    title=opp.get("title", f"Opportunity {i}"),
                    description=f"{opp.get('underserved_need', '')}\n\nProposed Solution: {opp.get('proposed_solution', '')}",
                    affected_users=report_dict.get("target_audience", {}).get("primary_segment", ""),
                    existing_solutions=opp.get("why_existing_fail", ""),
                    solution_gaps=opp.get("underserved_need", ""),
                    evidence_summary=report_dict.get("executive_summary", ""),
                    claim_type="source_backed" if sources_data else "hypothesis",
                    scores=scores.get("dimensions", {}),
                    overall_score=scores.get("overall_score", 7.5),
                    source_ids=source_ids,
                    rank=i,
                    status="evaluated",
                )
                db.add(cand)

            session.status = "completed"
            session.progress_pct = 100
            session.current_step = "completed"
            session.step_message = "Opportunity validation report completed successfully."
            session.completed_at = datetime.now(timezone.utc)

            log = AuditLog(
                user_id=user_id,
                action="validate_opportunity",
                category="research",
                description=f"Opportunity validation completed: {query} ({len(sources_data)} sources)",
            )
            db.add(log)
            await db.commit()

        except Exception as e:
            logger.error(f"Error in research pipeline execution for session {session_id}: {e}", exc_info=True)
            session.status = "failed"
            session.progress_pct = 100
            session.current_step = "failed"
            session.error_message = str(e)
            session.step_message = f"Research pipeline encountered an error: {e}"
            await db.commit()


@router.post("/validate")
async def validate_opportunity(
    body: LiveResearchValidateRequest,
    background_tasks: BackgroundTasks,
    sync: bool = False,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Start Phase 1.5 Live Research & Opportunity Validation Engine.
    Creates a persistent research session and runs asynchronously by default.
    Frontend can poll GET /api/research/sessions/{id}/status for live progress
    and retrieve GET /api/research/sessions/{id}/report when completed.
    """
    session = ResearchSession(
        owner_id=user.id,
        query=body.query,
        domain=body.domain or "",
        target_users=body.target_users or "",
        geography=body.geography or "",
        constraints=body.constraints or "",
        status="queued",
        progress_pct=5,
        current_step="queued",
        step_message="Research session initialized and queued.",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    is_sync = sync or (body.sync is True)

    if is_sync:
        await execute_live_research_pipeline(
            session_id=session.id,
            user_id=user.id,
            query=body.query,
            domain=body.domain or "",
            target_users=body.target_users or "",
            geography=body.geography or "",
            constraints=body.constraints or "",
        )
        rep_res = await db.execute(
            select(ResearchReport).where(ResearchReport.session_id == session.id)
        )
        report_record = rep_res.scalar_one_or_none()
        await db.refresh(session)
        return {
            "session": session.to_dict(),
            "report": report_record.to_dict() if report_record else None,
            "message": "Opportunity research and validation report completed successfully.",
        }

    # Asynchronous background execution
    background_tasks.add_task(
        execute_live_research_pipeline,
        session_id=session.id,
        user_id=user.id,
        query=body.query,
        domain=body.domain or "",
        target_users=body.target_users or "",
        geography=body.geography or "",
        constraints=body.constraints or "",
    )

    return {
        "session": session.to_dict(),
        "status_url": f"/api/research/sessions/{session.id}/status",
        "report_url": f"/api/research/sessions/{session.id}/report",
        "message": "Research session started in background. Poll /api/research/sessions/{id}/status for progress.",
    }


def safe_iso(dt):
    if dt is None:
        return None
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lightweight progress polling endpoint for active or completed research sessions.
    Returns status, progress_pct, current_step, step_message, and completion flags.
    """
    result = await db.execute(
        select(ResearchSession)
        .options(selectinload(ResearchSession.report))
        .where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    if user and session.owner_id and session.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Research session not found")

    return {
        "session_id": session.id,
        "status": session.status,
        "progress_pct": getattr(session, "progress_pct", 0) or 0,
        "current_step": getattr(session, "current_step", "") or "",
        "step_message": getattr(session, "step_message", "") or "",
        "error_message": session.error_message,
        "used_live_search": session.used_live_search,
        "search_provider": session.search_provider,
        "has_report": bool(session.report is not None),
        "created_at": safe_iso(session.created_at),
        "completed_at": safe_iso(session.completed_at),
    }


@router.post("/sessions/{session_id}/cancel")
async def cancel_research_session(
    session_id: str,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an in-progress research session."""
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session or session.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Research session not found")

    if session.status not in ("completed", "failed", "cancelled"):
        session.status = "cancelled"
        session.current_step = "cancelled"
        session.step_message = "Research session was cancelled by user."
        await db.commit()

    return {"success": True, "status": "cancelled", "message": "Research session cancelled successfully."}


@router.get("/sessions/{session_id}/report")
async def get_session_report(
    session_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full 13-section research report for a session with progress-aware status codes."""
    result = await db.execute(
        select(ResearchSession)
        .options(selectinload(ResearchSession.report))
        .where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    if user and session.owner_id and session.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Research session not found")

    if session.report:
        return {"report": session.report.to_dict()}

    if session.status in ("queued", "searching", "extracting", "analyzing", "scoring"):
        raise HTTPException(
            status_code=409,
            detail=f"Research is still in progress (status: {session.status}, progress: {session.progress_pct}%)",
        )
    if session.status == "failed":
        raise HTTPException(
            status_code=422,
            detail=f"Research session failed: {session.error_message or 'Unknown error'}",
        )
    if session.status == "cancelled":
        raise HTTPException(
            status_code=410,
            detail="Research session was cancelled by user.",
        )

    raise HTTPException(status_code=404, detail="Research report not found for this session")


@router.get("/reports/{report_id}")
async def get_report_by_id(
    report_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full research report by report ID."""
    result = await db.execute(
        select(ResearchReport).where(ResearchReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Research report not found")

    if user and report.owner_id and report.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Research report not found")

    return {"report": report.to_dict()}


@router.post("/reports/{report_id}/blueprint-preview")
async def get_report_blueprint_preview(
    report_id: str,
    opportunity_index: int = 0,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an architectural blueprint preview for a research opportunity.
    Returns domain entities, workflows, traceability matrix, and deterministic blueprint_hash
    for explicit user review and cryptographic approval binding.
    """
    result = await db.execute(
        select(ResearchReport).where(ResearchReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Research report not found")

    if user and report.owner_id and report.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Research report not found")

    from backend.services.research_blueprint_adapter import research_blueprint_adapter
    blueprint = await research_blueprint_adapter.generate_research_grounded_blueprint(
        report=report,
        opportunity_index=opportunity_index,
    )

    return {
        "report_id": report.id,
        "blueprint_hash": blueprint.get("blueprint_hash"),
        "title": blueprint.get("title"),
        "domain_entities": blueprint.get("domain_entities", []),
        "domain_workflows": blueprint.get("domain_workflows", []),
        "research_intelligence": blueprint.get("research_intelligence", {}),
        "blueprint": blueprint,
    }


@router.post("/reports/{report_id}/convert-to-project")
async def convert_report_to_project(
    report_id: str,
    body: ConvertReportRequest,
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Bridge Phase 1.5 to Project Creation:
    Takes a validated opportunity from the research report and generates a project.
    Enforces backend cryptographic hash approval and experimental hypothesis confirmation.
    """
    result = await db.execute(
        select(ResearchReport).where(ResearchReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Research report not found")

    if report.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Research report not found")

    if not body.approved:
        raise HTTPException(
            status_code=400,
            detail="Explicit user approval is required to convert a research opportunity into a project.",
        )

    opps = report.identified_opportunities or []
    idx = max(0, min(body.opportunity_index, len(opps) - 1)) if opps else 0
    selected_opp = opps[idx] if opps else {}

    # Generate active research-grounded blueprint
    from backend.services.research_blueprint_adapter import research_blueprint_adapter
    blueprint = await research_blueprint_adapter.generate_research_grounded_blueprint(
        report=report,
        opportunity_index=idx,
    )
    active_hash = blueprint.get("blueprint_hash")

    # Safeguard 2 & 3: Cryptographic blueprint hash validation & change invalidation
    if body.approved_blueprint_hash:
        if body.approved_blueprint_hash != active_hash:
            raise HTTPException(
                status_code=409,
                detail="Blueprint specification has changed since preview. Please re-review and approve the updated blueprint.",
            )

    # Safeguard: Experimental hypothesis quarantine enforcement
    hypotheses = blueprint.get("research_intelligence", {}).get("experimental_hypotheses", [])
    if hypotheses and not body.approve_experimental_hypotheses:
        # If user did not approve experimental hypotheses, filter them out of active traceability and workflows
        filtered_matrix = [
            req for req in blueprint.get("research_intelligence", {}).get("traceability_matrix", [])
            if req.get("evidence_classification") != "hypothesis"
        ]
        blueprint["research_intelligence"]["traceability_matrix"] = filtered_matrix
        blueprint["research_intelligence"]["experimental_hypotheses_approved"] = False
    else:
        blueprint["research_intelligence"]["experimental_hypotheses_approved"] = True

    proj_title = body.title or selected_opp.get("title") or report.title
    fallback_prefix = ""
    if not getattr(report, "used_live_search", False):
        fallback_prefix = "[CURATED FALLBACK DATA] "

    proj_desc = (
        body.description or
        f"{fallback_prefix}{selected_opp.get('underserved_need', '')}\n\nProposed Solution: {selected_opp.get('proposed_solution', '')}".strip() or
        report.executive_summary
    )

    # Link to problem candidate if exists
    cand_res = await db.execute(
        select(ProblemCandidate).where(ProblemCandidate.session_id == report.session_id)
    )
    cands = cand_res.scalars().all()
    selected_cand = cands[idx] if idx < len(cands) else (cands[0] if cands else None)

    # Seed initial development tasks from actionable recommendations
    import uuid
    initial_tasks = []
    for step_item in (report.actionable_recommendations or []):
        initial_tasks.append({
            "id": str(uuid.uuid4())[:8],
            "title": step_item.get("step", "Milestone Task"),
            "description": step_item.get("action", ""),
            "status": "pending",
            "timeline": step_item.get("timeline", "Sprint 1"),
        })

    project = Project(
        owner_id=user.id,
        name=proj_title[:100],
        description=proj_desc,
        problem_id=selected_cand.id if selected_cand else None,
        research_report_id=report.id,
        status="created",
        current_stage="architect",
        blueprint=blueprint,
        tech_stack=blueprint.get("tech_stack", {}),
        tasks=initial_tasks,
    )
    db.add(project)

    log = AuditLog(
        user_id=user.id, action="create_project_from_research", category="projects",
        description=f"Created project '{proj_title}' from research report {report.id}",
    )
    db.add(log)
    await db.commit()
    await db.refresh(project)

    return {
        "project": project.to_dict(),
        "message": "Project created successfully from research opportunity.",
    }
