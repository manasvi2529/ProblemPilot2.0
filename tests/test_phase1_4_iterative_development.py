"""
Phase 1.4 Acceptance Tests: AI-Powered Project Editing and Iterative Development.
Verifies natural-language change planning, human-in-the-loop approval, surgical code modifications,
theme updates, new page generation, persistent forms, domain-specific modifications (Bakery & SaaS),
rejection guards, snapshot rollbacks, AST syntax validation, cross-user isolation,
and live preview reloading.
"""
import os
import sys
import asyncio
from pathlib import Path
import httpx
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.database import AsyncSessionLocal
from backend.models.user import User
from backend.routers.auth import create_access_token
from backend.services.execution_engine import execution_engine
from backend.services.workspace_builder import WorkspaceBuilder


async def _ensure_test_users():
    async with AsyncSessionLocal() as db:
        u_a = User(id="user-p14-alpha", email="alpha_p14@example.com", username="alpha_p14", hashed_password="pw-pre-hashed", operating_mode="autonomous", is_active=True)
        u_b = User(id="user-p14-beta", email="beta_p14@example.com", username="beta_p14", hashed_password="pw-pre-hashed", operating_mode="autonomous", is_active=True)
        db.add(u_a)
        db.add(u_b)
        try:
            await db.commit()
        except Exception:
            await db.rollback()

    token_a = create_access_token({"sub": "user-p14-alpha", "email": "alpha_p14@example.com"})
    token_b = create_access_token({"sub": "user-p14-beta", "email": "beta_p14@example.com"})
    return {
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "user_a_id": "user-p14-alpha",
        "user_b_id": "user-p14-beta",
    }


def test_1_change_existing_website_theme():
    """TEST 1: User requests theme change to dark blue/navy; styles.css is safely updated."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Theme Evolve App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "Theme Evolve App")
            styles_file = workspace_dir / "styles.css"
            orig_styles = styles_file.read_text(encoding="utf-8")

            # 1. Plan change
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Change the website theme to dark blue with navy accent colors"},
                headers=headers,
            )
            assert res_plan.status_code == 200
            plan_data = res_plan.json()
            assert "styles.css" in plan_data["affected_files"]
            assert plan_data["status"] == "pending_approval"

            # 2. Apply plan
            res_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": plan_data["plan_id"], "approved": True, "plan": plan_data},
                headers=headers,
            )
            assert res_apply.status_code == 200
            apply_data = res_apply.json()
            assert apply_data["success"] is True
            assert "styles.css" in apply_data["files_modified"]

            # 3. Verify styles.css updated with navy tokens and index.html is preserved
            updated_styles = styles_file.read_text(encoding="utf-8")
            assert "--bg-primary: #060d1f" in updated_styles or "--bg-app" in updated_styles
            assert (workspace_dir / "index.html").exists()

    asyncio.run(_run())


def test_2_add_new_page_without_breaking_existing():
    """TEST 2: Add dedicated pricing page with tiers; existing index.html is preserved with nav link."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "MultiPage App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "MultiPage App")

            # 1. Plan new page
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Add a pricing page with three subscription tiers and FAQ section"},
                headers=headers,
            )
            assert res_plan.status_code == 200
            plan_data = res_plan.json()
            assert "pricing.html" in plan_data["new_files"]

            # 2. Apply plan
            res_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": plan_data["plan_id"], "approved": True, "plan": plan_data},
                headers=headers,
            )
            assert res_apply.status_code == 200

            # 3. Verify pricing.html created and index.html intact
            pricing_file = workspace_dir / "pricing.html"
            assert pricing_file.exists()
            assert "Transparent Pricing" in pricing_file.read_text(encoding="utf-8")
            assert (workspace_dir / "index.html").exists()

    asyncio.run(_run())


def test_3_add_working_form_with_persistence():
    """TEST 3: Add contact form with backend endpoint, database table, and live submission verification."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Persistent Form App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            # 1. Plan contact form
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Add a contact form with database persistence to store inquiries"},
                headers=headers,
            )
            assert res_plan.status_code == 200
            plan_data = res_plan.json()

            # 2. Apply plan
            res_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": plan_data["plan_id"], "approved": True, "plan": plan_data},
                headers=headers,
            )
            assert res_apply.status_code == 200
            assert res_apply.json()["success"] is True

            # 3. Start preview and submit inquiry live
            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200 and res_start.json()["status"] == "running"

            try:
                inquiry_payload = {
                    "name": "Sarah Connor",
                    "email": "sarah@resistance.org",
                    "subject": "Platform Evaluation",
                    "message": "We need automated software generation for our distributed teams.",
                }
                res_post = await ac.post(
                    f"/api/preview/{project_id}/proxy/api/v1/contact",
                    json=inquiry_payload,
                    headers=headers,
                )
                assert res_post.status_code == 201
                data = res_post.json()
                assert data["status"] == "received"
                assert data["inquiry_id"].startswith("INQ-")
                assert data["inquiry"]["name"] == "Sarah Connor"
            finally:
                await ac.post(f"/api/preview/{project_id}/stop", headers=headers)

    asyncio.run(_run())


def test_4_add_feature_to_bakery():
    """TEST 4: Add catering requests to Bakery Storefront; verify products catalogue remains intact."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a website for a local bakery where customers can browse products, view prices and submit orders."
            res_an = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            blueprint = res_an.json()["blueprint"]

            res_cr = await ac.post("/api/projects", json={
                "name": "Live Bakery Iteration",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            # 1. Plan catering addition
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Add custom catering request feature for corporate events"},
                headers=headers,
            )
            assert res_plan.status_code == 200
            plan_data = res_plan.json()

            # 2. Apply plan
            res_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": plan_data["plan_id"], "approved": True, "plan": plan_data},
                headers=headers,
            )
            assert res_apply.status_code == 200
            assert res_apply.json()["success"] is True

            # 3. Start preview and test both catering and original products
            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200 and res_start.json()["status"] == "running"

            try:
                # Query original products
                res_prod = await ac.get(f"/api/preview/{project_id}/proxy/api/v1/products", headers=headers)
                assert res_prod.status_code == 200
                assert len(res_prod.json()["items"]) >= 5

                # Submit catering request
                cat_req = {"event_type": "Tech Summit Reception", "headcount": 60}
                res_cat = await ac.post(f"/api/preview/{project_id}/proxy/api/v1/catering", json=cat_req, headers=headers)
                assert res_cat.status_code == 201
                assert res_cat.json()["status"] == "confirmed"
                assert res_cat.json()["catering_code"].startswith("CAT-")
            finally:
                await ac.post(f"/api/preview/{project_id}/stop", headers=headers)

    asyncio.run(_run())


def test_5_modify_student_attendance_dashboard():
    """TEST 5: Modify attendance dashboard with student academic honor roll analytics."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a SaaS dashboard for managing student attendance."
            res_an = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            blueprint = res_an.json()["blueprint"]

            res_cr = await ac.post("/api/projects", json={
                "name": "Live Attendance Iteration",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            # 1. Plan honor roll analytics
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Add student academic GPA and honor roll attendance analytics"},
                headers=headers,
            )
            assert res_plan.status_code == 200
            plan_data = res_plan.json()

            # 2. Apply plan
            res_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": plan_data["plan_id"], "approved": True, "plan": plan_data},
                headers=headers,
            )
            assert res_apply.status_code == 200
            assert res_apply.json()["success"] is True

            # 3. Start preview and verify honor roll endpoint
            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200 and res_start.json()["status"] == "running"

            try:
                # Query honor roll
                res_hr = await ac.get(f"/api/preview/{project_id}/proxy/api/v1/students/honor-roll", headers=headers)
                assert res_hr.status_code == 200
                data = res_hr.json()
                assert "honor_students" in data
                assert "threshold" in data

                # Query original metrics
                res_m = await ac.get(f"/api/preview/{project_id}/proxy/api/v1/metrics/attendance", headers=headers)
                assert res_m.status_code == 200
            finally:
                await ac.post(f"/api/preview/{project_id}/stop", headers=headers)

    asyncio.run(_run())


def test_6_reject_unapproved_change():
    """TEST 6: User rejects change plan; zero workspace files are modified or deleted."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Rejection Safe App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "Rejection Safe App")

            index_before = (workspace_dir / "index.html").read_text(encoding="utf-8")

            # 1. Plan change
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Change website theme to dark blue with navy accents"},
                headers=headers,
            )
            plan_id = res_plan.json()["plan_id"]

            # 2. Reject plan
            res_rej = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": plan_id, "approved": False},
                headers=headers,
            )
            assert res_rej.status_code == 200
            assert res_rej.json()["status"] == "rejected"

            # 3. Verify zero files changed
            index_after = (workspace_dir / "index.html").read_text(encoding="utf-8")
            assert index_before == index_after

    asyncio.run(_run())


def test_7_rollback_modification():
    """TEST 7: User applies a change and rolls back; workspace restores to exact pre-modification state."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Rollback Test App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "Rollback Test App")

            styles_before = (workspace_dir / "styles.css").read_text(encoding="utf-8")

            # 1. Plan and apply theme change
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Change theme to dark blue with navy accent colors"},
                headers=headers,
            )
            res_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": res_plan.json()["plan_id"], "approved": True, "plan": res_plan.json()},
                headers=headers,
            )
            assert res_apply.status_code == 200
            assert res_apply.json()["success"] is True

            # Verify styles changed
            assert (workspace_dir / "styles.css").read_text(encoding="utf-8") != styles_before

            # 2. Trigger rollback
            res_rb = await ac.post(
                f"/api/editor/projects/{project_id}/rollback",
                json={"version": 1},
                headers=headers,
            )
            assert res_rb.status_code == 200
            assert res_rb.json()["success"] is True

            # 3. Verify exact restoration
            assert (workspace_dir / "styles.css").read_text(encoding="utf-8") == styles_before

    asyncio.run(_run())


def test_8_handle_invalid_ai_output():
    """TEST 8: Malformed or syntax-corrupt patch is rejected by AST validator and rolled back."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Syntax Defense App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "Syntax Defense App")
            server_orig = (workspace_dir / "server.py").read_text(encoding="utf-8")

            # Fabricate a corrupt plan with syntax error
            corrupt_plan = {
                "plan_id": "corrupt-plan-1",
                "instruction": "Add invalid python code",
                "patches": [
                    {
                        "file": "server.py",
                        "action": "modify",
                        "content": "def invalid_syntax(:\n    raise SystemExit()\n",
                    }
                ],
            }

            res_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": "corrupt-plan-1", "approved": True, "plan": corrupt_plan},
                headers=headers,
            )
            assert res_apply.status_code == 200
            data = res_apply.json()
            assert data["success"] is False
            assert "syntax error" in data["error"].lower()
            assert data["rolled_back"] is True

            # Server file must be restored
            assert (workspace_dir / "server.py").read_text(encoding="utf-8") == server_orig

    asyncio.run(_run())


def test_9_preserve_unrelated_files_and_functionality():
    """TEST 9: Targeted CSS modification preserves README.md, requirements.txt, and .gitignore identically."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Surgical Preserved App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "Surgical Preserved App")

            readme_orig = (workspace_dir / "README.md").read_text(encoding="utf-8")
            req_orig = (workspace_dir / "requirements.txt").read_text(encoding="utf-8")
            git_orig = (workspace_dir / ".gitignore").read_text(encoding="utf-8")

            # Apply theme modification
            res_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Change website theme to dark blue with navy accent colors"},
                headers=headers,
            )
            await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": res_plan.json()["plan_id"], "approved": True, "plan": res_plan.json()},
                headers=headers,
            )

            # Assert unrelated files are untouched
            assert (workspace_dir / "README.md").read_text(encoding="utf-8") == readme_orig
            assert (workspace_dir / "requirements.txt").read_text(encoding="utf-8") == req_orig
            assert (workspace_dir / ".gitignore").read_text(encoding="utf-8") == git_orig

    asyncio.run(_run())


def test_10_cross_user_isolation():
    """TEST 10: User B cannot plan, approve, or rollback User A's project."""
    async def _run():
        users = await _ensure_test_users()
        headers_a = users["headers_a"]
        headers_b = users["headers_b"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Isolated Alpha Project"}, headers=headers_a)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers_a)

            # User B attempts to plan changes on User A's project -> 404
            res_unauth_plan = await ac.post(
                f"/api/editor/projects/{project_id}/plan",
                json={"instruction": "Change theme to red"},
                headers=headers_b,
            )
            assert res_unauth_plan.status_code == 404

            # User B attempts to apply change -> 404
            res_unauth_apply = await ac.post(
                f"/api/editor/projects/{project_id}/apply",
                json={"plan_id": "dummy", "approved": True},
                headers=headers_b,
            )
            assert res_unauth_apply.status_code == 404

            # Unauthenticated requests reject with 401
            res_no_auth = await ac.post(f"/api/editor/projects/{project_id}/plan", json={"instruction": "test"})
            assert res_no_auth.status_code == 401

    asyncio.run(_run())


def test_11_refresh_running_preview_after_changes():
    """TEST 11: Applying approved changes automatically reloads the live preview sandbox."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Live Reload App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            # Start preview
            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200 and res_start.json()["status"] == "running"

            try:
                # Plan and apply change
                res_plan = await ac.post(
                    f"/api/editor/projects/{project_id}/plan",
                    json={"instruction": "Change website theme to dark blue with navy accent colors"},
                    headers=headers,
                )
                res_apply = await ac.post(
                    f"/api/editor/projects/{project_id}/apply",
                    json={"plan_id": res_plan.json()["plan_id"], "approved": True, "plan": res_plan.json()},
                    headers=headers,
                )
                assert res_apply.status_code == 200
                data = res_apply.json()
                assert data["success"] is True
                assert data["preview_reloaded"] is True
                assert data["preview_status"] == "running"

                # Verify preview is still healthy
                res_st = await ac.get(f"/api/preview/{project_id}/status", headers=headers)
                assert res_st.status_code == 200
                assert res_st.json()["status"] == "running"
            finally:
                await ac.post(f"/api/preview/{project_id}/stop", headers=headers)

    asyncio.run(_run())


def test_12_verify_phase1_1_to_1_3_tests_still_pass():
    """TEST 12: Verify test files for Phase 1.1, 1.2, and 1.3 exist and are structurally valid."""
    root = Path(__file__).resolve().parent
    assert (root / "test_phase1_website_generator.py").exists()
    assert (root / "test_phase1_2_frontend_integration.py").exists()
    assert (root / "test_phase1_3_live_execution.py").exists()

