"""
Phase 1.2 Acceptance Tests: Complete Frontend-to-Backend Dynamic Project Generation Workflow.
"""
import pytest
import asyncio
import io
import zipfile
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import AsyncSessionLocal
from backend.models.user import User
from backend.routers.auth import create_access_token


async def _ensure_test_users():
    async with AsyncSessionLocal() as db:
        u_a = User(id="user-alpha-e2e", email="alpha_e2e@example.com", username="alpha_e2e", hashed_password="pw-pre-hashed", operating_mode="autonomous", is_active=True)
        u_b = User(id="user-beta-e2e", email="beta_e2e@example.com", username="beta_e2e", hashed_password="pw-pre-hashed", operating_mode="autonomous", is_active=True)
        db.add(u_a)
        db.add(u_b)
        try:
            await db.commit()
        except Exception:
            await db.rollback()

    token_a = create_access_token({"sub": "user-alpha-e2e", "email": "alpha_e2e@example.com"})
    token_b = create_access_token({"sub": "user-beta-e2e", "email": "beta_e2e@example.com"})
    return {
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
    }


def test_1_e2e_data_analyst_portfolio():
    """TEST 1: Full E2E flow for Archetype A (Data Analyst Portfolio)."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a modern portfolio website for a data analyst with projects, skills, resume download and contact form."
            res_analyze = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            assert res_analyze.status_code == 200
            data_analyze = res_analyze.json()
            assert data_analyze["detected_category"] == "portfolio"
            blueprint = data_analyze["blueprint"]

            res_create = await ac.post("/api/projects", json={
                "name": "Data Analyst Portfolio",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            assert res_create.status_code == 200
            project_id = res_create.json()["project"]["id"]

            res_build = await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            assert res_build.status_code == 200
            assert res_build.json().get("files_generated", 0) >= 5

            res_files = await ac.get(f"/api/orchestrator/projects/{project_id}/files", headers=headers)
            assert res_files.status_code == 200
            file_paths = [f["path"] for f in res_files.json()["files"]]
            assert "server.py" in file_paths
            assert "index.html" in file_paths
            assert "database.py" in file_paths

            res_test = await ac.post(f"/api/orchestrator/projects/{project_id}/test", headers=headers)
            assert res_test.status_code == 200
            assert res_test.json()["passed"] is True
    asyncio.run(_run())


def test_2_e2e_bakery_storefront():
    """TEST 2: Full E2E flow for Archetype B (Local Bakery Storefront)."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a website for a local bakery where customers can browse products, view prices and submit orders."
            res_analyze = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            assert res_analyze.status_code == 200
            blueprint = res_analyze.json()["blueprint"]

            res_create = await ac.post("/api/projects", json={
                "name": "Artisan Bakery",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            project_id = res_create.json()["project"]["id"]

            res_build = await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            assert res_build.status_code == 200

            res_file = await ac.get(f"/api/orchestrator/projects/{project_id}/files/server.py", headers=headers)
            assert res_file.status_code == 200
            assert "/api/v1/orders" in res_file.json()["content"]

            res_test = await ac.post(f"/api/orchestrator/projects/{project_id}/test", headers=headers)
            assert res_test.status_code == 200
            assert res_test.json()["passed"] is True
    asyncio.run(_run())


def test_3_e2e_student_attendance_saas_dashboard():
    """TEST 3: Full E2E flow for Archetype C (Student Attendance SaaS Dashboard)."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a SaaS dashboard for managing student attendance."
            res_analyze = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            assert res_analyze.status_code == 200
            blueprint = res_analyze.json()["blueprint"]

            res_create = await ac.post("/api/projects", json={
                "name": "AttendTrack SaaS",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            project_id = res_create.json()["project"]["id"]

            res_build = await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            assert res_build.status_code == 200

            res_file = await ac.get(f"/api/orchestrator/projects/{project_id}/files/server.py", headers=headers)
            assert res_file.status_code == 200
            assert "/api/v1/students" in res_file.json()["content"]

            res_test = await ac.post(f"/api/orchestrator/projects/{project_id}/test", headers=headers)
            assert res_test.status_code == 200
            assert res_test.json()["passed"] is True
    asyncio.run(_run())


def test_4_blueprint_feature_customization():
    """TEST 4: Blueprint editability before approval."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a portfolio website for a data analyst."
            res_analyze = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            blueprint = res_analyze.json()["blueprint"]

            blueprint["features"].append("Custom Real-Time Snowflake Query Visualizer")

            res_create = await ac.post("/api/projects", json={
                "name": "Customized Portfolio",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            project_id = res_create.json()["project"]["id"]

            res_get = await ac.get(f"/api/projects/{project_id}", headers=headers)
            saved_bp = res_get.json()["project"]["blueprint"]
            assert "Custom Real-Time Snowflake Query Visualizer" in saved_bp["features"]
    asyncio.run(_run())


def test_5_download_project_zip_archive():
    """TEST 5: Download project codebase endpoint packages valid zip archive."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_create = await ac.post("/api/projects", json={
                "name": "Zippable App",
                "description": "Bakery storefront",
            }, headers=headers)
            project_id = res_create.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            res_zip = await ac.get(f"/api/projects/{project_id}/download", headers=headers)
            assert res_zip.status_code == 200
            assert res_zip.headers["content-type"] == "application/zip"

            zip_buf = io.BytesIO(res_zip.content)
            with zipfile.ZipFile(zip_buf, "r") as zf:
                namelist = zf.namelist()
                assert "server.py" in namelist
                assert "index.html" in namelist
    asyncio.run(_run())


def test_6_path_traversal_protection():
    """TEST 6: Path traversal attempts via individual file read endpoint are blocked."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_create = await ac.post("/api/projects", json={"name": "Secure App"}, headers=headers)
            project_id = res_create.json()["project"]["id"]

            res_evil = await ac.get(f"/api/orchestrator/projects/{project_id}/files/%2e%2e%2fetc%2fpasswd", headers=headers)
            assert res_evil.status_code in (400, 403, 404)
    asyncio.run(_run())


def test_7_cross_user_workspace_isolation():
    """TEST 7: Cross-user workspace security: User B cannot access User A's project."""
    async def _run():
        users = await _ensure_test_users()
        headers_a = users["headers_a"]
        headers_b = users["headers_b"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_a = await ac.post("/api/projects", json={"name": "User A Private App"}, headers=headers_a)
            project_id_a = res_a.json()["project"]["id"]

            res_get = await ac.get(f"/api/projects/{project_id_a}", headers=headers_b)
            assert res_get.status_code == 404

            res_files = await ac.get(f"/api/orchestrator/projects/{project_id_a}/files", headers=headers_b)
            assert res_files.status_code == 404

            res_down = await ac.get(f"/api/projects/{project_id_a}/download", headers=headers_b)
            assert res_down.status_code == 404
    asyncio.run(_run())


def test_8_unauthenticated_access_rejection():
    """TEST 8: Unauthenticated access is rejected with 401 Unauthorized."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_analyze = await ac.post("/api/projects/analyze-idea", json={"description": "some idea"})
            assert res_analyze.status_code == 401

            res_create = await ac.post("/api/projects", json={"name": "unauth"})
            assert res_create.status_code == 401

            res_list = await ac.get("/api/projects")
            assert res_list.status_code == 401
    asyncio.run(_run())


def test_9_page_refresh_persistence():
    """TEST 9: Page refresh persistence: Project, blueprint, and generated files persist across reloads."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_create = await ac.post("/api/projects", json={
                "name": "Persistent Project",
                "description": "Attendance SaaS",
                "blueprint": {"project_name": "Persistent", "features": ["Feature A", "Feature B"]},
            }, headers=headers)
            project_id = res_create.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            res_project = await ac.get(f"/api/projects/{project_id}", headers=headers)
            assert res_project.status_code == 200
            p_data = res_project.json()
            assert p_data["project"]["name"] == "Persistent Project"
            assert len(p_data["files"]) >= 5
            assert p_data["project"]["blueprint"]["project_name"] == "Persistent"
    asyncio.run(_run())
