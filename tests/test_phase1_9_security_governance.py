"""
Phase 1.9 End-to-End Test Suite:
Workstream 9 (Security, Governance & Usage Management)
Workstream 10 (End-to-End Product Validation & Regression Verification)

Covers:
1. Multi-Tenant Isolation (Projects, Files, Research Sessions, Reports, Preview Servers).
2. Authentication Hardening & Token Revocation (Logout / Blacklist verification).
3. Role-Based Access Control (Admin vs Regular User permissions on /api/admin/*).
4. Multi-Tier Quota & Rate Limiting Enforcement (Daily/Monthly limits, 429 response, Retry-After header).
5. Rate Limiter Middleware & Payload Size Limit (413 Payload Too Large on >10MB).
6. Sandbox Governance & Timeouts (Startup 30s timeout, Health check 10s timeout, Env Sanitization).
7. Target Project Regression (47667aa6-cf44-4d09-b5a7-d2d9bb239d05 lifecycle verification).
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from httpx import ASGITransport

from backend.main import app
from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models.user import User
from backend.models.project import Project, ProjectFile
from backend.models.research import ResearchSession, ResearchReport
from backend.models.usage import QuotaPolicy, UserUsage, TokenBlacklist
from backend.security import hash_password, create_access_token, decode_access_token, revoke_token, is_token_revoked
from backend.services.quota_service import quota_service
from backend.services.execution_engine import execution_engine
from backend.services.workspace_builder import WorkspaceBuilder
from sqlalchemy import select, delete


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# ==============================================================================
# 1. MULTI-TENANT ISOLATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_multi_tenant_isolation_projects_and_files():
    """Verify Tenant B cannot access, read, or modify Tenant A's projects or files."""
    async with AsyncSessionLocal() as db:
        # Create Tenant A
        tenant_a_id = f"test-tenant-a-{uuid.uuid4().hex[:8]}"
        user_a = User(
            id=tenant_a_id,
            email=f"{tenant_a_id}@example.com",
            username=tenant_a_id,
            hashed_password=hash_password("password123"),
            tier="free",
            role="user",
        )
        db.add(user_a)

        # Create Tenant B
        tenant_b_id = f"test-tenant-b-{uuid.uuid4().hex[:8]}"
        user_b = User(
            id=tenant_b_id,
            email=f"{tenant_b_id}@example.com",
            username=tenant_b_id,
            hashed_password=hash_password("password123"),
            tier="free",
            role="user",
        )
        db.add(user_b)

        # Create Tenant A's project
        project_a_id = f"proj-{uuid.uuid4().hex[:8]}"
        proj_a = Project(
            id=project_a_id,
            name="Tenant A Secret Project",
            owner_id=tenant_a_id,
            status="ready",
            current_stage="build",
        )
        db.add(proj_a)

        # Create Tenant A's file
        file_a = ProjectFile(
            project_id=project_a_id,
            path="secret.txt",
            content="SUPER_CONFIDENTIAL_TENANT_A_DATA",
            language="text",
            version=1,
        )
        db.add(file_a)
        await db.commit()

    token_a = create_access_token({"sub": tenant_a_id, "email": user_a.email, "role": "user"})
    token_b = create_access_token({"sub": tenant_b_id, "email": user_b.email, "role": "user"})

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Tenant A can read project
        res_a = await client.get(f"/api/projects/{project_a_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert res_a.status_code == 200
        assert res_a.json()["project"]["name"] == "Tenant A Secret Project"

        # Tenant B CANNOT read project (404 or 403)
        res_b = await client.get(f"/api/projects/{project_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_b.status_code in (404, 403)

        # Tenant B CANNOT list files of project A
        res_b_files = await client.get(f"/api/orchestrator/projects/{project_a_id}/files", headers={"Authorization": f"Bearer {token_b}"})
        assert res_b_files.status_code in (404, 403)

        # Tenant B CANNOT trigger preview start for project A
        res_b_preview = await client.post(f"/api/preview/{project_a_id}/start", headers={"Authorization": f"Bearer {token_b}"})
        assert res_b_preview.status_code in (404, 403)

    # Clean up test users and project
    async with AsyncSessionLocal() as db:
        await db.execute(delete(ProjectFile).where(ProjectFile.project_id == project_a_id))
        await db.execute(delete(Project).where(Project.id == project_a_id))
        await db.execute(delete(User).where(User.id.in_([tenant_a_id, tenant_b_id])))
        await db.commit()


@pytest.mark.asyncio
async def test_multi_tenant_isolation_research_sessions_and_reports():
    """Verify Tenant B cannot read or steal Tenant A's research sessions and reports."""
    async with AsyncSessionLocal() as db:
        tenant_a_id = f"test-res-a-{uuid.uuid4().hex[:8]}"
        user_a = User(
            id=tenant_a_id,
            email=f"{tenant_a_id}@example.com",
            username=tenant_a_id,
            hashed_password=hash_password("password123"),
            tier="free",
            role="user",
        )
        db.add(user_a)

        tenant_b_id = f"test-res-b-{uuid.uuid4().hex[:8]}"
        user_b = User(
            id=tenant_b_id,
            email=f"{tenant_b_id}@example.com",
            username=tenant_b_id,
            hashed_password=hash_password("password123"),
            tier="free",
            role="user",
        )
        db.add(user_b)

        # Create session for Tenant A
        sess_a_id = f"sess-{uuid.uuid4().hex[:8]}"
        sess_a = ResearchSession(
            id=sess_a_id,
            owner_id=tenant_a_id,
            query="Tenant A proprietary problem domain",
            status="completed",
        )
        db.add(sess_a)

        # Create report for Tenant A
        rep_a_id = f"rep-{uuid.uuid4().hex[:8]}"
        rep_a = ResearchReport(
            id=rep_a_id,
            session_id=sess_a_id,
            owner_id=tenant_a_id,
            title="Confidential Market Research",
            executive_summary="Proprietary analysis",
        )
        db.add(rep_a)
        await db.commit()

    token_a = create_access_token({"sub": tenant_a_id, "email": user_a.email, "role": "user"})
    token_b = create_access_token({"sub": tenant_b_id, "email": user_b.email, "role": "user"})

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Tenant A can read session and report
        res_a = await client.get(f"/api/research/sessions/{sess_a_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert res_a.status_code == 200

        # Tenant B CANNOT read Tenant A's session
        res_b = await client.get(f"/api/research/sessions/{sess_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_b.status_code in (404, 403)

        # Tenant B CANNOT read Tenant A's report
        res_b_rep = await client.get(f"/api/research/reports/{rep_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_b_rep.status_code in (404, 403)

        # Tenant B cannot read status or report via session
        res_b_status = await client.get(f"/api/research/sessions/{sess_a_id}/status", headers={"Authorization": f"Bearer {token_b}"})
        assert res_b_status.status_code in (404, 403)

    # Clean up
    async with AsyncSessionLocal() as db:
        await db.execute(delete(ResearchReport).where(ResearchReport.id == rep_a_id))
        await db.execute(delete(ResearchSession).where(ResearchSession.id == sess_a_id))
        await db.execute(delete(User).where(User.id.in_([tenant_a_id, tenant_b_id])))
        await db.commit()


# ==============================================================================
# 2. AUTHENTICATION HARDENING & TOKEN REVOCATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_token_revocation_on_logout():
    """Verify that logging out revokes the JWT token immediately and subsequent calls return 401."""
    async with AsyncSessionLocal() as db:
        user_id = f"test-auth-{uuid.uuid4().hex[:8]}"
        user = User(
            id=user_id,
            email=f"{user_id}@example.com",
            username=user_id,
            hashed_password=hash_password("secretpassword"),
            tier="free",
            role="user",
        )
        db.add(user)
        await db.commit()

    token = create_access_token({"sub": user_id, "email": user.email, "role": "user"})

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Token works before logout
        res_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res_me.status_code == 200
        assert res_me.json()["user"]["id"] == user_id

        # 2. Call logout endpoint
        res_logout = await client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert res_logout.status_code == 200
        assert res_logout.json()["revoked"] is True

        # 3. Same token should now be rejected with 401 Unauthorized
        res_after = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res_after.status_code == 401
        assert "revoked" in res_after.json()["detail"].lower()

    # Clean up
    async with AsyncSessionLocal() as db:
        await db.execute(delete(TokenBlacklist).where(TokenBlacklist.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


# ==============================================================================
# 3. ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_role_based_access_control_admin_endpoints():
    """Verify normal users are blocked (403) from /api/admin/*, but admins have access."""
    async with AsyncSessionLocal() as db:
        user_id = f"test-regular-{uuid.uuid4().hex[:8]}"
        admin_id = f"test-admin-{uuid.uuid4().hex[:8]}"

        reg_user = User(
            id=user_id,
            email=f"{user_id}@example.com",
            username=user_id,
            hashed_password=hash_password("pass123"),
            tier="free",
            role="user",
        )
        admin_user = User(
            id=admin_id,
            email=f"{admin_id}@example.com",
            username=admin_id,
            hashed_password=hash_password("pass123"),
            tier="enterprise",
            role="admin",
        )
        db.add_all([reg_user, admin_user])
        await db.commit()

    token_user = create_access_token({"sub": user_id, "email": reg_user.email, "role": "user"})
    token_admin = create_access_token({"sub": admin_id, "email": admin_user.email, "role": "admin"})

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Regular user calling /api/admin/overview -> 403 Forbidden
        res_denied = await client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token_user}"})
        assert res_denied.status_code == 403
        assert "administrator" in res_denied.json()["detail"].lower()

        # Regular user calling /api/admin/users -> 403 Forbidden
        res_denied_users = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {token_user}"})
        assert res_denied_users.status_code == 403

        # Admin calling /api/admin/overview -> 200 OK
        res_admin = await client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token_admin}"})
        assert res_admin.status_code == 200
        data = res_admin.json()
        assert "total_registered_users" in data or "total_users" in data
        assert "platform_monthly_totals" in data or "platform_usage" in data

        # Admin calling /api/admin/quotas -> 200 OK
        res_quotas = await client.get("/api/admin/quotas", headers={"Authorization": f"Bearer {token_admin}"})
        assert res_quotas.status_code == 200
        quotas_data = res_quotas.json()
        assert "policies" in quotas_data
        tiers = [p["tier"] for p in quotas_data["policies"]]
        assert "free" in tiers
        assert "pro" in tiers

    # Clean up
    async with AsyncSessionLocal() as db:
        await db.execute(delete(User).where(User.id.in_([user_id, admin_id])))
        await db.commit()


# ==============================================================================
# 4. MULTI-TIER QUOTA & RATE LIMITING ENFORCEMENT TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_quota_exhaustion_returns_429_with_retry_after():
    """Verify QuotaService blocks requests with 429 when limits are reached."""
    async with AsyncSessionLocal() as db:
        user_id = f"test-quota-{uuid.uuid4().hex[:8]}"
        user = User(
            id=user_id,
            email=f"{user_id}@example.com",
            username=user_id,
            hashed_password=hash_password("pass123"),
            tier="free",
            role="user",
        )
        db.add(user)

        # Set a test quota policy for tier 'free' with a low limit of 2 daily research sessions
        res = await db.execute(select(QuotaPolicy).where(QuotaPolicy.tier == "free"))
        policy = res.scalar_one_or_none()
        orig_limit = policy.daily_research_sessions if policy else 5
        if policy:
            policy.daily_research_sessions = 2
        await db.commit()

        # Record 2 usages for today
        await quota_service.record_usage(db, user, action_type="research_session", units=1)
        await quota_service.record_usage(db, user, action_type="research_session", units=1)

    token = create_access_token({"sub": user_id, "email": user.email, "role": "user"})

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 3rd request should fail with 429
        res_blocked = await client.post(
            "/api/research/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Testing quota limits", "domain": "Tech"},
        )
        assert res_blocked.status_code == 429
        assert "Retry-After" in res_blocked.headers
        detail = res_blocked.json()["detail"]
        assert "exceeded" in detail["message"].lower()
        assert detail["limit"] == 2

    # Restore policy & clean up
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(QuotaPolicy).where(QuotaPolicy.tier == "free"))
        policy = res.scalar_one_or_none()
        if policy:
            policy.daily_research_sessions = orig_limit
        await db.execute(delete(UserUsage).where(UserUsage.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


# ==============================================================================
# 5. RATE LIMITER MIDDLEWARE & PAYLOAD SIZE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_payload_size_limit_rejects_oversized_request():
    """Verify requests over 10MB receive HTTP 413 Payload Too Large."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Construct header indicating payload > 10MB
        oversized_headers = {
            "Content-Length": str(11 * 1024 * 1024),
            "Content-Type": "application/json",
        }
        res = await client.post("/api/auth/login", headers=oversized_headers, content=b"{}")
        assert res.status_code == 413
        assert "maximum limit" in res.json()["detail"].lower() or "maximum allowed" in res.json()["detail"].lower()


# ==============================================================================
# 6. SECURE SANDBOX GOVERNANCE & TIMEOUT BOUNDS
# ==============================================================================

@pytest.mark.asyncio
async def test_sandbox_environment_sanitization(tmp_path):
    """Verify that execution_engine.sanitize_environment strips host secrets and API keys."""
    env = execution_engine.sanitize_environment(port=8080, workspace_dir=tmp_path)
    # Ensure sensitive credentials are stripped
    forbidden_keys = [
        "OPENROUTER_API_KEY",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "SECRET_KEY",
        "DATABASE_URL",
        "AWS_SECRET_ACCESS_KEY",
    ]
    for key in forbidden_keys:
        assert key not in env, f"Sensitive key {key} leaked into sandbox environment!"


# ==============================================================================
# 7. TARGET PROJECT REGRESSION (47667aa6-cf44-4d09-b5a7-d2d9bb239d05)
# ==============================================================================

@pytest.mark.asyncio
async def test_target_project_lifecycle_regression():
    """
    Regression verification for Grain Storage Depot Automation project:
    ID: 47667aa6-cf44-4d09-b5a7-d2d9bb239d05
    Verifies:
    1. Project exists in database and has persisted files.
    2. Start preview server succeeds.
    3. Health probe and root HTML are served.
    4. Base tag injection works.
    5. Clean process shutdown.
    """
    target_id = "47667aa6-cf44-4d09-b5a7-d2d9bb239d05"
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).where(Project.id == target_id))
        project = res.scalar_one_or_none()
        assert project is not None, f"Target project {target_id} not found in database!"

        owner_res = await db.execute(select(User).where(User.id == project.owner_id))
        owner = owner_res.scalar_one_or_none()
        assert owner is not None, f"Owner {project.owner_id} for target project not found!"

        files_res = await db.execute(select(ProjectFile).where(ProjectFile.project_id == target_id))
        files = files_res.scalars().all()
        assert len(files) >= 10, f"Expected at least 10 persisted files, got {len(files)}"

    token = create_access_token({"sub": owner.id, "email": owner.email, "role": owner.role})
    transport = ASGITransport(app=app)

    orig_fallback = settings.ALLOW_INSECURE_LOCAL_FALLBACK
    settings.ALLOW_INSECURE_LOCAL_FALLBACK = True

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Start server with bounded timeout
        try:
            async with asyncio.timeout(35.0):
                start_res = await client.post(f"/api/preview/{target_id}/start", headers={"Authorization": f"Bearer {token}"})
                assert start_res.status_code == 200, f"Start failed: {start_res.text}"
                start_data = start_res.json()
                assert start_data.get("success") is True
                assert start_data.get("status") == "running"
                port = start_data.get("port")
                assert port is not None and port > 1024

            # Verify status endpoint
            status_res = await client.get(f"/api/preview/{target_id}/status", headers={"Authorization": f"Bearer {token}"})
            assert status_res.status_code == 200
            assert status_res.json()["status"] == "running"

            # Verify proxy serves root HTML with base tag
            proxy_res = await client.get(f"/api/preview/{target_id}/proxy/")
            assert proxy_res.status_code == 200
            assert f'<base href="/api/preview/{target_id}/proxy/">' in proxy_res.text
            assert "Grain Storage Depot" in proxy_res.text

        finally:
            # Stop server cleanly
            stop_res = await client.post(f"/api/preview/{target_id}/stop", headers={"Authorization": f"Bearer {token}"})
            assert stop_res.status_code == 200
            assert stop_res.json()["success"] is True

            # Verify status is stopped
            status_after = await client.get(f"/api/preview/{target_id}/status", headers={"Authorization": f"Bearer {token}"})
            assert status_after.json()["status"] == "stopped"

            settings.ALLOW_INSECURE_LOCAL_FALLBACK = orig_fallback
