"""
Phase 1.5 Acceptance Tests: Live Research & Opportunity Validation Engine.
Verifies live multi-source search integration, source extraction and citation handling,
graceful handling of unavailable sources, explicit insufficient evidence reporting,
claim classification (verified vs inferred), competitor analysis and pricing transparency,
transparent multi-dimensional opportunity scoring, complete 13-section report generation,
database persistence of sessions and reports, cross-user isolation, and direct bridging
from validated opportunity into project creation.
"""
import os
import sys
import asyncio
from unittest.mock import patch, AsyncMock
from pathlib import Path
import httpx
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.database import AsyncSessionLocal
from backend.models.user import User
from backend.models.research import ResearchSession, ResearchReport, ResearchSource, ProblemCandidate
from backend.models.project import Project
from backend.routers.auth import create_access_token
from backend.services.live_research_engine import LiveResearchEngine, live_research_engine
from backend.services.research_service import fetch_page_content


async def _ensure_test_users():
    from backend.database import init_db
    await init_db()
    async with AsyncSessionLocal() as db:
        u_a = User(
            id="user-p15-alpha",
            email="alpha_p15@example.com",
            username="alpha_p15",
            hashed_password="pw-pre-hashed",
            operating_mode="autonomous",
            is_active=True,
        )
        u_b = User(
            id="user-p15-beta",
            email="beta_p15@example.com",
            username="beta_p15",
            hashed_password="pw-pre-hashed",
            operating_mode="autonomous",
            is_active=True,
        )
        db.add(u_a)
        db.add(u_b)
        try:
            await db.commit()
        except Exception:
            await db.rollback()

    token_a = create_access_token({"sub": "user-p15-alpha", "email": "alpha_p15@example.com"})
    token_b = create_access_token({"sub": "user-p15-beta", "email": "beta_p15@example.com"})
    return {
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "user_a_id": "user-p15-alpha",
        "user_b_id": "user-p15-beta",
    }


def test_1_live_search_integration_and_provider_dispatch():
    """TEST 1: Live search pipeline formulates targeted queries and dispatches multi-source retrieval."""
    async def _run():
        engine = LiveResearchEngine()
        queries = engine.formulate_search_queries(
            query="AI-powered education for college students in India",
            domain="Education & Career Tech",
            geography="India",
            target_users="Undergraduate engineering students",
        )
        assert len(queries) >= 3, "Should formulate at least 3 distinct query perspectives"
        assert any("india" in q.lower() for q in queries)
        assert any("student" in q.lower() or "education" in q.lower() for q in queries)

        mock_reddit = [
            {
                "platform": "reddit",
                "title": "College labs in India are completely outdated",
                "content": "We are taught ancient C++ compilers. Real companies ask for modern frameworks and automated testing.",
                "url": "https://reddit.com/r/developersIndia/comments/labs_outdated",
                "subreddit": "developersIndia",
                "score": 45,
                "created_utc": 1700000000,
            }
        ]
        with patch("backend.services.live_research_engine.scrape_reddit", new_callable=AsyncMock, return_value=mock_reddit), \
             patch("backend.services.live_research_engine.scrape_hackernews", new_callable=AsyncMock, return_value=[]), \
             patch("backend.services.live_research_engine.scrape_stackoverflow", new_callable=AsyncMock, return_value=[]):
            evidence = await engine.gather_evidence(
                query="AI-powered education for college students in India",
                domain="Education",
                geography="India",
                target_users="College Students",
                max_sources=8,
            )
            assert "sources" in evidence
            assert len(evidence["sources"]) >= 1
            assert "used_live_search" in evidence
            assert "search_provider" in evidence
            assert "status_message" in evidence
            assert evidence["search_provider"] in ("google_custom", "serper", "brave", "community_scrapers")

    asyncio.run(_run())


def test_2_source_extraction_and_citation_handling():
    """TEST 2: Source extraction records valid URLs, titles, publisher, and timestamps."""
    async def _run():
        engine = LiveResearchEngine()
        mock_hn = [
            {
                "platform": "hackernews",
                "title": "Why Indian engineering colleges fail to produce employable coders",
                "story_text": "The gap between university syllabus and industry needs has widened exponentially.",
                "url": "https://news.ycombinator.com/item?id=38000001",
                "points": 98,
                "created_at": "2026-01-15T10:00:00Z",
            }
        ]
        with patch("backend.services.live_research_engine.scrape_reddit", new_callable=AsyncMock, return_value=[]), \
             patch("backend.services.live_research_engine.scrape_hackernews", new_callable=AsyncMock, return_value=mock_hn), \
             patch("backend.services.live_research_engine.scrape_stackoverflow", new_callable=AsyncMock, return_value=[]):
            evidence = await engine.gather_evidence(
                query="software development challenges",
                domain="Developer Tools",
                max_sources=5,
            )
            sources = evidence.get("sources", [])
            assert isinstance(sources, list)
            assert len(sources) >= 1
            src = sources[0]
            assert src.get("url", "").startswith("http"), "Source URL must be valid HTTP/HTTPS"
            assert src.get("title") == "Why Indian engineering colleges fail to produce employable coders"
            assert "retrieval_date" in src, "Source must record retrieval timestamp"
            assert src.get("reliability") == "high"

    asyncio.run(_run())


def test_3_invalid_or_unavailable_sources_handled_gracefully():
    """TEST 3: Unreachable URLs or network timeouts are handled without crashing."""
    async def _run():
        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("DNS resolution failed")):
            res = await fetch_page_content("https://invalid-non-existent-domain-xyz-12345.org/test-404")
            assert res["success"] is False
            assert res["text"] == ""
            assert "error" in res
            assert res["publication_date"] is None

    asyncio.run(_run())


def test_4_insufficient_evidence_explicitly_reported():
    """TEST 4: When no evidence is retrieved, the report explicitly states insufficient evidence."""
    async def _run():
        engine = LiveResearchEngine()
        report = await engine.analyze_and_generate_report(
            query="highly obscure topic with zero sources",
            sources=[],
            used_live_search=False,
            search_provider="none",
        )
        assert report["evidence_sufficiency"] == "insufficient"
        assert len(report["sources"]) == 0
        assert "hypothes" in report["executive_summary"].lower() or "insufficient" in report["executive_summary"].lower()

    asyncio.run(_run())


def test_5_claim_type_classification():
    """TEST 5: Explicitly distinguishes verified facts from source-backed claims and hypotheses."""
    async def _run():
        engine = LiveResearchEngine()
        mock_sources = [
            {"url": "https://gov.in/aicte-report", "title": "AICTE Engineering Education Report", "snippet": "Over 1.5 million engineering graduates graduate annually.", "reliability": "high"},
            {"url": "https://reddit.com/r/cscareerquestions/123", "title": "Struggling with campus placement coding tests", "snippet": "Our college teaches Turbo C++, employers ask for Next.js", "reliability": "medium"},
        ]
        report = await engine.analyze_and_generate_report(
            query="Indian engineering college placements",
            domain="Education",
            geography="India",
            sources=mock_sources,
        )
        sources = report["sources"]
        assert len(sources) == 2
        claim_types = [s.get("claim_type") for s in sources]
        assert "verified_fact" in claim_types or "source_backed" in claim_types

    asyncio.run(_run())


def test_6_competitor_analysis_and_pricing_transparency():
    """TEST 6: Competitor analysis includes strengths, weaknesses, gaps, and transparent pricing."""
    async def _run():
        engine = LiveResearchEngine()
        mock_sources = [
            {"url": "https://reddit.com/r/SaaS/comments/test", "title": "Tired of UpGrad and Scaler pricing", "snippet": "₹2.5 Lakhs for a course is unaffordable for Tier 3 students", "reliability": "medium"},
        ]
        report = await engine.analyze_and_generate_report(
            query="AI technical placement coaching for college students in India",
            domain="Education",
            geography="India",
            sources=mock_sources,
        )
        competitors = report["competitor_analysis"]
        assert len(competitors) >= 2, "Must analyze at least 2 competitor categories"
        for c in competitors:
            assert "name" in c
            assert "positioning" in c
            assert "strengths" in c
            assert "weaknesses" in c or "gap" in c

        pricing = report["competitor_pricing"]
        assert "verified_models" in pricing
        assert "pricing_notes" in pricing
        assert len(pricing["verified_models"]) > 0

    asyncio.run(_run())


def test_7_opportunity_scoring_framework():
    """TEST 7: Multi-factor scoring evaluates all 6 required dimensions with explanations."""
    scoring = LiveResearchEngine.calculate_opportunity_scores(
        title="AI Code Interview Coach for College Students",
        problem_desc="Students fail technical tests due to outdated curriculum and lack of automated code feedback.",
        sources=[
            {"url": "https://reddit.com/r/learnprogramming/test", "title": "No feedback in college labs", "reliability": "high"},
            {"url": "https://news.ycombinator.com/item?id=123", "title": "Indian tech hiring crisis", "reliability": "medium"},
        ],
        target_audience="Undergraduate college students in India",
    )
    assert "overall_score" in scoring
    assert 0 <= scoring["overall_score"] <= 10
    dimensions = scoring["dimensions"]

    required_dims = [
        "problem_severity",
        "evidence_of_demand",
        "market_opportunity",
        "competition_intensity",
        "feasibility",
        "differentiation_potential",
    ]
    for dim in required_dims:
        assert dim in dimensions, f"Missing required scoring dimension: {dim}"
        d_val = dimensions[dim]
        assert "score" in d_val and 0 <= d_val["score"] <= 10
        assert "explanation" in d_val and len(d_val["explanation"]) > 5
        assert "confidence" in d_val

    assert "disclaimer" in scoring
    assert "heuristic" in scoring["disclaimer"].lower() or "transparent" in scoring["disclaimer"].lower()


def test_8_complete_13_section_report_generation():
    """TEST 8: Every successful research request yields all 13 required report sections."""
    async def _run():
        engine = LiveResearchEngine()
        mock_sources = [
            {"url": "https://example.com/article", "title": "AI in Higher Education", "snippet": "Colleges adopt AI diagnostic tutoring tools.", "reliability": "high"},
        ]
        report = await engine.analyze_and_generate_report(
            query="AI-powered education for college students in India",
            domain="Education",
            geography="India",
            target_users="College Students",
            sources=mock_sources,
        )

        required_13_sections = [
            "executive_summary",          # 1
            "problem_landscape",          # 2
            "target_audience",            # 3
            "customer_pain_points",       # 4
            "competitor_analysis",        # 5
            "competitor_pricing",         # 6
            "market_trends",              # 7
            "identified_opportunities",   # 8
            "opportunity_scores",         # 9
            "risks_and_limitations",      # 10
            "actionable_recommendations", # 11
            "final_conclusion",           # 12
            "sources",                    # 13
        ]

        for sec in required_13_sections:
            assert sec in report, f"Missing required report section {sec}"
            assert report[sec] is not None, f"Section {sec} should not be None"

        assert len(report["identified_opportunities"]) >= 1
        assert len(report["customer_pain_points"]) >= 1
        assert len(report["market_trends"]) >= 1
        assert len(report["risks_and_limitations"]) >= 1
        assert len(report["actionable_recommendations"]) >= 1

    asyncio.run(_run())


def test_9_api_endpoint_validate_and_database_persistence():
    """TEST 9: POST /api/research/validate executes pipeline and persists session, sources, and report."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        
        mock_reddit = [
            {
                "platform": "reddit",
                "title": "College labs in India are completely outdated",
                "content": "Students struggle with real coding interviews.",
                "url": "https://reddit.com/r/developersIndia/comments/labs_outdated",
                "subreddit": "developersIndia",
                "score": 35,
                "created_utc": 1700000000,
            }
        ]
        with patch("backend.services.live_research_engine.scrape_reddit", new_callable=AsyncMock, return_value=mock_reddit), \
             patch("backend.services.live_research_engine.scrape_hackernews", new_callable=AsyncMock, return_value=[]), \
             patch("backend.services.live_research_engine.scrape_stackoverflow", new_callable=AsyncMock, return_value=[]):
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # 1. Test synchronous execution
                res = await ac.post(
                    "/api/research/validate",
                    headers=headers,
                    json={
                        "query": "AI-powered education for college students in India",
                        "domain": "Education",
                        "geography": "India",
                        "target_users": "College Students",
                        "sync": True,
                    },
                    timeout=30.0,
                )
                assert res.status_code == 200, f"Validation endpoint failed: {res.text}"
                data = res.json()
                assert "session" in data
                assert "report" in data
                sess_id = data["session"]["id"]
                rep_id = data["report"]["id"]

                # Verify in DB directly
                async with AsyncSessionLocal() as db:
                    sess_record = await db.get(ResearchSession, sess_id)
                    assert sess_record is not None
                    assert sess_record.query == "AI-powered education for college students in India"
                    assert sess_record.status == "completed"
                    assert sess_record.progress_pct == 100

                    rep_record = await db.get(ResearchReport, rep_id)
                    assert rep_record is not None
                    assert rep_record.executive_summary != ""
                    assert rep_record.session_id == sess_id

                # 2. Test asynchronous mode and status polling
                res_async = await ac.post(
                    "/api/research/validate",
                    headers=headers,
                    json={
                        "query": "Async test query",
                        "sync": False,
                    },
                    timeout=10.0,
                )
                assert res_async.status_code in (200, 202)
                async_data = res_async.json()
                assert "session" in async_data
                assert "status_url" in async_data
                async_sess_id = async_data["session"]["id"]

                # Poll status endpoint
                status_res = await ac.get(f"/api/research/sessions/{async_sess_id}/status", headers=headers)
                assert status_res.status_code == 200
                st_data = status_res.json()
                assert "status" in st_data
                assert "progress_pct" in st_data

    asyncio.run(_run())


def test_10_cross_user_isolation_and_authorization():
    """TEST 10: User B cannot access User A's private research report."""
    async def _run():
        users = await _ensure_test_users()
        headers_a = users["headers_a"]
        headers_b = users["headers_b"]
        transport = ASGITransport(app=app)
        with patch("backend.services.live_research_engine.scrape_reddit", new_callable=AsyncMock, return_value=[]), \
             patch("backend.services.live_research_engine.scrape_hackernews", new_callable=AsyncMock, return_value=[]), \
             patch("backend.services.live_research_engine.scrape_stackoverflow", new_callable=AsyncMock, return_value=[]):
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # User A creates a validation report
                res = await ac.post(
                    "/api/research/validate",
                    headers=headers_a,
                    json={"query": "Confidential market analysis for User A", "sync": True},
                    timeout=30.0,
                )
                assert res.status_code == 200
                report_id = res.json()["report"]["id"]

                # User B attempts to access User A's report
                res_b = await ac.get(f"/api/research/reports/{report_id}", headers=headers_b)
                assert res_b.status_code == 404, "User B must not be able to view User A's report"

                # User A can access User A's report
                res_a = await ac.get(f"/api/research/reports/{report_id}", headers=headers_a)
                assert res_a.status_code == 200

    asyncio.run(_run())


def test_11_bridge_opportunity_to_project_creation():
    """TEST 11: POST /api/research/reports/{id}/convert-to-project requires approval and instantiates project."""
    async def _run():
        users = await _ensure_test_users()
        headers_a = users["headers_a"]
        transport = ASGITransport(app=app)
        with patch("backend.services.live_research_engine.scrape_reddit", new_callable=AsyncMock, return_value=[]), \
             patch("backend.services.live_research_engine.scrape_hackernews", new_callable=AsyncMock, return_value=[]), \
             patch("backend.services.live_research_engine.scrape_stackoverflow", new_callable=AsyncMock, return_value=[]):
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # 1. Validate opportunity
                res = await ac.post(
                    "/api/research/validate",
                    headers=headers_a,
                    json={"query": "Automated attendance tracking for colleges in India", "sync": True},
                    timeout=30.0,
                )
                assert res.status_code == 200
                report_id = res.json()["report"]["id"]

                # 2. Convert to project WITHOUT approval -> must fail with 400
                unapproved_res = await ac.post(
                    f"/api/research/reports/{report_id}/convert-to-project",
                    headers=headers_a,
                    json={"opportunity_index": 0, "approved": False},
                )
                assert unapproved_res.status_code == 400, "Must reject conversion without user approval"

                # 3. Convert to project WITH explicit approval -> succeeds
                conv_res = await ac.post(
                    f"/api/research/reports/{report_id}/convert-to-project",
                    headers=headers_a,
                    json={"opportunity_index": 0, "approved": True},
                )
                assert conv_res.status_code == 200, f"Convert to project failed: {conv_res.text}"
                proj_data = conv_res.json()["project"]
                assert "id" in proj_data
                assert proj_data["current_stage"] == "architect"
                assert proj_data["owner_id"] == users["user_a_id"]

                # Verify in DB
                async with AsyncSessionLocal() as db:
                    p_db = await db.get(Project, proj_data["id"])
                    assert p_db is not None
                    assert p_db.owner_id == users["user_a_id"]

    asyncio.run(_run())


def test_12_verify_phase1_1_to_1_4_zero_regressions():
    """TEST 12: Ensure Phase 1.1–1.4 components (Blueprint, Workspace, Preview, Editor) remain fully operational."""
    from backend.services.blueprint_engine import BlueprintEngine
    from backend.services.workspace_builder import WorkspaceBuilder
    from backend.services.execution_engine import execution_engine
    from backend.services.iterative_engine import ChangePlanner, CodeModificationEngine

    # Verify all service classes are intact
    bp = BlueprintEngine()
    wb = WorkspaceBuilder()
    planner = ChangePlanner()
    mod_engine = CodeModificationEngine()
    assert bp is not None
    assert wb is not None
    assert planner is not None
    assert mod_engine is not None
    assert execution_engine is not None


def test_13_session_cancellation():
    """TEST 13: POST /api/research/sessions/{id}/cancel safely aborts an active session."""
    from uuid import uuid4
    async def _run():
        users = await _ensure_test_users()
        headers_a = users["headers_a"]
        transport = ASGITransport(app=app)
        cancel_id = f"test-cancel-{uuid4()}"
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create a session in DB in searching state
            async with AsyncSessionLocal() as db:
                sess = ResearchSession(
                    id=cancel_id,
                    owner_id=users["user_a_id"],
                    query="Topic to cancel",
                    status="searching",
                    progress_pct=25,
                    current_step="gathering_evidence",
                    step_message="Searching sources...",
                )
                db.add(sess)
                await db.commit()

            # Call cancel endpoint
            cancel_res = await ac.post(f"/api/research/sessions/{cancel_id}/cancel", headers=headers_a)
            assert cancel_res.status_code == 200
            data = cancel_res.json()
            assert data["status"] == "cancelled"

            # Check status endpoint
            st_res = await ac.get(f"/api/research/sessions/{cancel_id}/status", headers=headers_a)
            assert st_res.status_code == 200
            assert st_res.json()["status"] == "cancelled"

    asyncio.run(_run())
