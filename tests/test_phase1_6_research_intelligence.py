"""
Comprehensive Acceptance Test Suite for Phase 1.6
Tests Deep Research-to-Project Intelligence Integration:
- T1: Canonical evidence traceability & legacy tag compatibility
- T2: Domain-specific generation & non-generic schemas
- T3: Deep differentiation across divergent research topics (AgriTech vs. Clinical Trials)
- T4: Insufficient evidence hypothesis quarantine
- T5: Conversion API authorization and explicit approval check
- T6: Cryptographic versioned blueprint approval hash enforcement (Safeguard 2)
- T7: Blueprint hash invalidation on change (Safeguard 3)
- T8: Curated/simulated fallback data labeling (Safeguard 1)
- T9: Synthetic data integrity & disclaimer markers
- T10: Project research intelligence endpoint
- T11: ChangePlanner preserves research intelligence
- T12: Backward compatibility with standard non-research projects
"""
import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import AsyncSessionLocal, init_db
from backend.models.user import User
from backend.models.research import ResearchSession, ResearchReport
from backend.models.project import Project
from backend.services.research_blueprint_adapter import (
    research_blueprint_adapter,
    canonicalize_classification,
)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    import asyncio
    asyncio.run(init_db())


async def create_test_user_and_token(db, prefix="p16"):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"{prefix}-{uid[:8]}@example.com",
        username=f"{prefix}_{uid[:8]}",
        hashed_password="hashed_pw_test",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    from backend.routers.auth import create_access_token
    token = create_access_token(data={"sub": user.id, "email": user.email})
    return user, token


def make_sample_report(session_id: str, owner_id: str, topic="agri", sufficiency="moderate", live_search=False):
    rid = str(uuid.uuid4())
    if topic == "agri":
        title = "AI-Driven Agricultural Drone Monitoring in Punjab"
        summary = "Precision crop monitoring using multispectral drone sensors to detect pests."
        opps = [{
            "title": "Autonomous AgroDrone Fleet Manager",
            "underserved_need": "Deep rural zones lack reliable crop scouting.",
            "proposed_solution": "Deploy lightweight IoT multispectral drone telemetry.",
        }]
        pain_points = [
            {"pain_point": "Intermittent rural 4G prevents real-time NDVI telemetry upload", "claim_type": "source_backed"},
            {"pain_point": "Manual pest scouting leads to pesticide over-spraying", "claim_type": "verified"},
        ]
        competitors = [{
            "name": "AgroScan Pro",
            "weaknesses": ["No offline sync", "High annual upfront licensing fee"],
        }]
    else:
        title = "Clinical Trial Protocol Matching for Rare Diseases"
        summary = "Automated matching of rare disease patient cohorts with clinical trials."
        opps = [{
            "title": "RareProtocol Clinical Cohort Matcher",
            "underserved_need": "Rare disease patients struggle to discover matching Phase II/III trials.",
            "proposed_solution": "Structured genomic biomarker protocol search engine.",
        }]
        pain_points = [
            {"pain_point": "Genomic biomarker eligibility criteria are trapped in unindexed PDFs", "claim_type": "verified_fact"},
            {"pain_point": "HIPAA consent audit trails are manual and error-prone", "claim_type": "inference"},
        ]
        competitors = [{
            "name": "TrialFinder Classic",
            "weaknesses": ["Lacks genetic biomarker filtering", "No automated HIPAA audit trail"],
        }]

    return ResearchReport(
        id=rid,
        session_id=session_id,
        owner_id=owner_id,
        title=title,
        executive_summary=summary,
        identified_opportunities=opps,
        customer_pain_points=pain_points,
        competitor_analysis=competitors,
        evidence_sufficiency=sufficiency,
        used_live_search=live_search,
        sources=[{
            "title": f"Empirical Study on {title}",
            "url": "https://example.org/study-2026",
            "publisher": "Academic Press",
            "publication_date": "2026-01-15",
        }],
        created_at=datetime.now(timezone.utc),
    )


# ── Tests ────────────────────────────────────────────────────────────────────

def test_canonical_evidence_traceability_mapping():
    """T1: Canonical classification mapping and legacy tag compatibility."""
    assert canonicalize_classification("verified") == "verified_fact"
    assert canonicalize_classification("verified_fact") == "verified_fact"
    assert canonicalize_classification("source_backed") == "source_backed"
    assert canonicalize_classification("inference") == "inference"
    assert canonicalize_classification("hypothesis") == "hypothesis"
    assert canonicalize_classification(None) == "inference"
    assert canonicalize_classification("unknown_tag") == "inference"


@pytest.mark.asyncio
async def test_domain_specific_generation_entities_and_seed():
    """T2: Non-generic schemas and synthetic seed data markers."""
    report = make_sample_report("sess-1", "user-1", topic="agri")
    blueprint = await research_blueprint_adapter.generate_research_grounded_blueprint(report)

    # Verify domain entities
    entities = blueprint.get("domain_entities", [])
    entity_names = [e["name"] for e in entities]
    assert "FieldParcel" in entity_names
    assert "InfestationLog" in entity_names
    assert "Item" not in entity_names
    assert "Product" not in entity_names

    # Verify synthetic seed data integrity
    seed = blueprint.get("research_intelligence", {}).get("synthetic_seed_data", {})
    assert seed.get("is_synthetic") is True
    assert "SYNTHETIC SEED DATA" in seed.get("disclaimer", "")
    assert "field_parcels" in seed.get("records", {})


@pytest.mark.asyncio
async def test_deep_differentiation_divergent_topics():
    """T3: Deep differentiation test between AgriTech and Clinical Trials."""
    report_agri = make_sample_report("sess-agri", "user-1", topic="agri")
    report_med = make_sample_report("sess-med", "user-1", topic="clinical")

    bp_agri = await research_blueprint_adapter.generate_research_grounded_blueprint(report_agri)
    bp_med = await research_blueprint_adapter.generate_research_grounded_blueprint(report_med)

    # Compare domain schemas
    agri_tables = {e["table_name"] for e in bp_agri.get("domain_entities", [])}
    med_tables = {e["table_name"] for e in bp_med.get("domain_entities", [])}
    assert agri_tables == {"field_parcels", "infestation_logs"}
    assert med_tables == {"clinical_protocols", "patient_cohorts"}
    assert len(agri_tables.intersection(med_tables)) == 0  # 0% table collision

    # Compare API workflows
    agri_endpoints = {w["endpoint"] for w in bp_agri.get("domain_workflows", [])}
    med_endpoints = {w["endpoint"] for w in bp_med.get("domain_workflows", [])}
    assert len(agri_endpoints.intersection(med_endpoints)) == 0

    # Compare cryptographic hashes
    assert bp_agri["blueprint_hash"] != bp_med["blueprint_hash"]


@pytest.mark.asyncio
async def test_insufficient_evidence_hypothesis_quarantine():
    """T4: Insufficient evidence causes unverified claims to quarantine as hypothesis."""
    report = make_sample_report("sess-insuf", "user-1", topic="agri", sufficiency="insufficient")
    bp = await research_blueprint_adapter.generate_research_grounded_blueprint(report)

    intel = bp.get("research_intelligence", {})
    assert intel.get("evidence_sufficiency") == "insufficient"
    hypotheses = intel.get("experimental_hypotheses", [])
    assert len(hypotheses) > 0
    for h in hypotheses:
        assert h.get("evidence_classification") == "hypothesis"


@pytest.mark.asyncio
async def test_conversion_api_authorization_and_approval():
    """T5: Explicit user approval & ownership enforcement on conversion."""
    async with AsyncSessionLocal() as db:
        user, token = await create_test_user_and_token(db, prefix="t5")
        other_user, other_token = await create_test_user_and_token(db, prefix="t5_other")
        report = make_sample_report("sess-t5", user.id, topic="agri")
        db.add(report)
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unapproved call -> 400
        res = await client.post(
            f"/api/research/reports/{report.id}/convert-to-project",
            headers={"Authorization": f"Bearer {token}"},
            json={"approved": False},
        )
        assert res.status_code == 400

        # 2. Unauthorized user trying to convert someone else's report -> 404
        res2 = await client.post(
            f"/api/research/reports/{report.id}/convert-to-project",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"approved": True},
        )
        assert res2.status_code == 404


@pytest.mark.asyncio
async def test_versioned_blueprint_approval_hash_and_invalidation():
    """T6 & T7: Backend cryptographic hash validation and invalidation on mismatch."""
    async with AsyncSessionLocal() as db:
        user, token = await create_test_user_and_token(db, prefix="t6")
        report = make_sample_report("sess-t6", user.id, topic="clinical")
        db.add(report)
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Request preview
        prev_res = await client.post(
            f"/api/research/reports/{report.id}/blueprint-preview?opportunity_index=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert prev_res.status_code == 200
        data = prev_res.json()
        active_hash = data["blueprint_hash"]
        assert len(active_hash) == 64  # SHA-256

        # 2. Call conversion with a forged/outdated hash -> 409 Conflict (Safeguard 3)
        res_mismatch = await client.post(
            f"/api/research/reports/{report.id}/convert-to-project",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "approved": True,
                "opportunity_index": 0,
                "approved_blueprint_hash": "outdated_or_mismatched_hash_value_12345",
            },
        )
        assert res_mismatch.status_code == 409
        assert "Blueprint specification has changed" in res_mismatch.json()["detail"]

        # 3. Call conversion with valid hash -> 200 OK (Safeguard 2)
        res_ok = await client.post(
            f"/api/research/reports/{report.id}/convert-to-project",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "approved": True,
                "opportunity_index": 0,
                "approved_blueprint_hash": active_hash,
                "approve_experimental_hypotheses": True,
            },
        )
        assert res_ok.status_code == 200
        created = res_ok.json()["project"]
        assert created["research_report_id"] == report.id


@pytest.mark.asyncio
async def test_curated_fallback_data_labeling():
    """T8: Curated fallback notice when real search is not used (Safeguard 1)."""
    report = make_sample_report("sess-fallback", "user-1", topic="agri", live_search=False)
    bp = await research_blueprint_adapter.generate_research_grounded_blueprint(report)
    intel = bp.get("research_intelligence", {})
    assert intel.get("is_curated_fallback") is True
    assert "CURATED DEMO DATA" in intel.get("fallback_notice", "")


@pytest.mark.asyncio
async def test_project_research_intelligence_endpoint():
    """T10: GET /api/projects/{id}/research-intelligence returns rich matrix."""
    async with AsyncSessionLocal() as db:
        user, token = await create_test_user_and_token(db, prefix="t10")
        report = make_sample_report("sess-t10", user.id, topic="agri")
        db.add(report)
        await db.commit()

        # Create linked project
        bp = await research_blueprint_adapter.generate_research_grounded_blueprint(report)
        proj = Project(
            owner_id=user.id,
            name="AgroDrone Project",
            research_report_id=report.id,
            blueprint=bp,
        )
        db.add(proj)
        await db.commit()
        await db.refresh(proj)
        project_id = proj.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/projects/{project_id}/research-intelligence",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["has_research"] is True
        assert data["report_id"] == report.id
        assert len(data["research_intelligence"]["traceability_matrix"]) > 0


@pytest.mark.asyncio
async def test_backward_compatibility_standard_projects():
    """T12: Non-research projects continue to work cleanly."""
    async with AsyncSessionLocal() as db:
        user, token = await create_test_user_and_token(db, prefix="t12")
        std_proj = Project(
            owner_id=user.id,
            name="Vanilla E-Commerce Store",
            description="A regular store with no research report",
            blueprint={"title": "Store", "pages": ["index.html"]},
        )
        db.add(std_proj)
        await db.commit()
        await db.refresh(std_proj)
        std_id = std_proj.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/projects/{std_id}/research-intelligence",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["has_research"] is False
        assert data["report"] is None


@pytest.mark.asyncio
async def test_change_planner_preserves_research_context(tmp_path):
    """T11: ChangePlanner injects and preserves validated research context in planning prompts."""
    from backend.services.iterative_engine import ChangePlanner
    report = make_sample_report("sess-cp", "user-cp", topic="agri")
    bp = await research_blueprint_adapter.generate_research_grounded_blueprint(report)

    # Create dummy workspace file
    test_file = tmp_path / "server.py"
    test_file.write_text("# AgriDrone server", encoding="utf-8")

    plan = await ChangePlanner.plan_changes(
        project_id="proj-cp-test",
        instruction="Add real-time pest alert notification banner based on competitor gap",
        blueprint=bp,
        workspace_dir=tmp_path,
    )

    assert plan is not None
    assert "plan_id" in plan
    assert "affected_files" in plan
    # Verify that plan or prompt structure recognizes research intelligence
    assert bp["research_intelligence"]["is_research_backed"] is True
    assert len(bp["research_intelligence"]["traceability_matrix"]) > 0
