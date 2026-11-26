"""
Comprehensive End-to-End Product Beta Test Suite:
1. Container Sandbox Isolation & Security Limits:
   - Verifies Docker command argument construction with non-root (1000:1000), CPU (0.5), Memory (512m), pids-limit (64), --security-opt no-new-privileges, and --cap-drop ALL.
   - Verifies that when Docker is unavailable and ALLOW_INSECURE_LOCAL_FALLBACK is False, preview start returns blocked status (does not run on host).
   - Verifies that when ALLOW_INSECURE_LOCAL_FALLBACK is True, local dev execution works cleanly.
2. Complete User Journey Lifecycle:
   - User registration & login.
   - Project creation with validated domain entities & tech stack.
   - Codebase synthesis and disk hydration.
   - Preview server startup, status inspection, health probe, and shutdown.
   - Token revocation on logout.
"""
import pytest
import asyncio
import uuid
import httpx
from httpx import ASGITransport
from pathlib import Path

from backend.main import app
from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models.user import User
from backend.models.project import Project, ProjectFile
from backend.services.container_engine import ContainerSandboxEngine
from backend.services.execution_engine import execution_engine
from backend.security import hash_password, create_access_token
from sqlalchemy import select, delete


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# ==============================================================================
# 1. CONTAINER SECURITY & RESTRICTION TESTS
# ==============================================================================

def test_container_sandbox_run_arguments_enforce_security_mandates(tmp_path):
    """
    Verify ContainerSandboxEngine.build_docker_run_args enforces:
    - Non-root user: --user 1000:1000
    - CPU limit: --cpus 0.5
    - Memory limit: --memory 512m --memory-swap 512m
    - Process limit: --pids-limit 64
    - Drop all capabilities: --cap-drop ALL --cap-add NET_BIND_SERVICE
    - No privilege escalation: --security-opt no-new-privileges:true
    - Network: --network bridge
    - Scoped workspace mount: -v <workspace>:/workspace:rw
    - Loopback host port binding: -p 127.0.0.1:8150:8150
    """
    port = 8150
    cmd = ["python", "-m", "http.server", "8150"]
    args = ContainerSandboxEngine.build_docker_run_args(
        container_name="test-sandbox-secure",
        workspace_dir=tmp_path,
        port=port,
        cmd=cmd,
        cpu_limit=0.5,
        memory_mb=512,
        pids_limit=64,
    )

    args_str = " ".join(args)
    assert "--user 1000:1000" in args_str
    assert "--cpus 0.5" in args_str
    assert "--memory 512m" in args_str
    assert "--memory-swap 512m" in args_str
    assert "--pids-limit 64" in args_str
    assert "--cap-drop ALL" in args_str
    assert "--cap-add NET_BIND_SERVICE" in args_str
    assert "--security-opt no-new-privileges:true" in args_str
    assert f"127.0.0.1:{port}:{port}" in args_str
    assert f"{tmp_path.resolve().as_posix()}:/workspace:rw" in args_str
    assert "docker.sock" not in args_str


@pytest.mark.asyncio
async def test_blocked_status_when_docker_unavailable_and_insecure_fallback_disabled(tmp_path):
    """
    Verify that if Docker is unavailable and ALLOW_INSECURE_LOCAL_FALLBACK is False,
    the execution engine refuses to execute on the host and returns a BLOCKED status.
    """
    # Create test dummy project
    dummy_project_id = f"test-sec-{uuid.uuid4().hex[:8]}"
    dummy_user_id = f"user-sec-{uuid.uuid4().hex[:8]}"
    index_file = tmp_path / "index.html"
    index_file.write_text("<h1>Secure App</h1>", encoding="utf-8")

    # Ensure fallback is disabled
    orig_fallback = settings.ALLOW_INSECURE_LOCAL_FALLBACK
    orig_mode = settings.EXECUTION_MODE
    try:
        settings.ALLOW_INSECURE_LOCAL_FALLBACK = False
        settings.EXECUTION_MODE = "docker"

        res = await execution_engine.start_project(
            project_id=dummy_project_id,
            user_id=dummy_user_id,
            workspace_dir=tmp_path,
        )

        # If Docker is not installed on this host, it must be BLOCKED
        if not ContainerSandboxEngine.is_docker_available():
            assert res.get("success") is False
            assert res.get("status") == "blocked"
            assert "CONTAINER_EXECUTION_UNAVAILABLE" in res.get("error")
    finally:
        settings.ALLOW_INSECURE_LOCAL_FALLBACK = orig_fallback
        settings.EXECUTION_MODE = orig_mode


# ==============================================================================
# 2. FULL USER JOURNEY E2E INTEGRATION
# ==============================================================================

@pytest.mark.asyncio
async def test_complete_user_journey_registration_project_preview_logout(tmp_path):
    """
    End-to-End User Journey:
    1. Register new user.
    2. Authenticate and verify user profile.
    3. Create a project with validated architecture.
    4. Generate and hydrate workspace files.
    5. Start preview in development mode (with ALLOW_INSECURE_LOCAL_FALLBACK=True).
    6. Verify live health check, status, and proxy rendering.
    7. Clean process termination.
    8. User logout and session revocation.
    """
    orig_fallback = settings.ALLOW_INSECURE_LOCAL_FALLBACK
    settings.ALLOW_INSECURE_LOCAL_FALLBACK = True

    unique_suffix = uuid.uuid4().hex[:8]
    test_email = f"beta_user_{unique_suffix}@example.com"
    test_username = f"beta_{unique_suffix}"
    test_password = "SecureBetaPassword123!"

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Step 1: Register
        reg_res = await client.post("/api/auth/register", json={
            "email": test_email,
            "username": test_username,
            "password": test_password,
            "full_name": "Beta Test User",
        })
        assert reg_res.status_code in (200, 201), f"Registration failed: {reg_res.text}"
        token = reg_res.json()["token"]
        user_id = reg_res.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Verify me
        me_res = await client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["user"]["username"] == test_username

        # Step 3: Create project
        proj_res = await client.post("/api/projects", headers=headers, json={
            "name": "Beta E2E SaaS Dashboard",
            "description": "Full stack project for beta verification",
            "tech_stack": {"frontend": "vanilla_html", "backend": "python"},
            "blueprint": {"title": "Beta Dashboard", "views": ["home", "analytics"]},
        })
        assert proj_res.status_code == 200, f"Project creation failed: {proj_res.text}"
        project_id = proj_res.json()["project"]["id"]

        # Step 4: Hydrate project files into DB
        async with AsyncSessionLocal() as db:
            html_content = "<!DOCTYPE html><html><head><title>Beta E2E App</title></head><body><h1>Beta Online</h1></body></html>"
            pf = ProjectFile(
                project_id=project_id,
                path="index.html",
                content=html_content,
                language="html",
                version=1,
            )
            db.add(pf)
            await db.commit()

        # Step 5: Start preview server
        try:
            start_res = await client.post(f"/api/preview/{project_id}/start", headers=headers)
            assert start_res.status_code == 200, f"Preview start failed: {start_res.text}"
            start_data = start_res.json()
            assert start_data["success"] is True
            assert start_data["status"] == "running"
            port = start_data["port"]

            # Step 6: Verify status & proxy
            status_res = await client.get(f"/api/preview/{project_id}/status", headers=headers)
            assert status_res.status_code == 200
            assert status_res.json()["status"] == "running"

            proxy_res = await client.get(f"/api/preview/{project_id}/proxy/")
            assert proxy_res.status_code == 200
            assert "Beta Online" in proxy_res.text
            assert f'<base href="/api/preview/{project_id}/proxy/">' in proxy_res.text

        finally:
            # Step 7: Stop preview server
            stop_res = await client.post(f"/api/preview/{project_id}/stop", headers=headers)
            assert stop_res.status_code == 200
            assert stop_res.json()["success"] is True

        # Step 8: Logout and revoke token
        logout_res = await client.post("/api/auth/logout", headers=headers)
        assert logout_res.status_code == 200
        assert logout_res.json()["revoked"] is True

        # Subsequent authenticated call must return 401
        after_logout = await client.get("/api/auth/me", headers=headers)
        assert after_logout.status_code == 401

    # Cleanup test records
    async with AsyncSessionLocal() as db:
        await db.execute(delete(ProjectFile).where(ProjectFile.project_id == project_id))
        await db.execute(delete(Project).where(Project.id == project_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()

    settings.ALLOW_INSECURE_LOCAL_FALLBACK = orig_fallback
