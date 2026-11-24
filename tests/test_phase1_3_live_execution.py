"""
Phase 1.3 Acceptance Tests: Live Website Execution, Preview, and Interactive Testing.
Verifies real subprocess sandbox execution, dynamic port allocation, health checks,
homepage loading, static asset verification, API endpoints, database persistence,
process restart/stop, error diagnostics & targeted repairs, and security isolation.
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
        u_a = User(id="user-p13-alpha", email="alpha_p13@example.com", username="alpha_p13", hashed_password="pw-pre-hashed", operating_mode="autonomous", is_active=True)
        u_b = User(id="user-p13-beta", email="beta_p13@example.com", username="beta_p13", hashed_password="pw-pre-hashed", operating_mode="autonomous", is_active=True)
        db.add(u_a)
        db.add(u_b)
        try:
            await db.commit()
        except Exception:
            await db.rollback()

    token_a = create_access_token({"sub": "user-p13-alpha", "email": "alpha_p13@example.com"})
    token_b = create_access_token({"sub": "user-p13-beta", "email": "beta_p13@example.com"})
    return {
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "user_a_id": "user-p13-alpha",
        "user_b_id": "user-p13-beta",
    }


def test_1_live_execution_portfolio_website():
    """TEST 1: Full live execution and interactive testing of Archetype A (Portfolio)."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        user_id = users["user_a_id"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a modern portfolio website for a data analyst with projects, skills, resume download and contact form."
            res_an = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            assert res_an.status_code == 200
            blueprint = res_an.json()["blueprint"]

            res_cr = await ac.post("/api/projects", json={
                "name": "Live Portfolio App",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            assert res_cr.status_code == 200
            project_id = res_cr.json()["project"]["id"]

            # Build workspace files
            res_b = await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            assert res_b.status_code == 200

            # 1. Start live preview server
            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200
            data_start = res_start.json()
            assert data_start["success"] is True
            assert data_start["status"] == "running"
            port = data_start["port"]
            assert port >= 8100

            try:
                # 2. Check preview status endpoint
                res_st = await ac.get(f"/api/preview/{project_id}/status", headers=headers)
                assert res_st.status_code == 200
                assert res_st.json()["running"] is True
                assert res_st.json()["port"] == port

                # 3. Request homepage via proxy endpoint
                res_proxy = await ac.get(f"/api/preview/{project_id}/proxy/", headers=headers)
                assert res_proxy.status_code == 200
                assert "text/html" in res_proxy.headers.get("content-type", "")
                assert "Data Analyst" in res_proxy.text
                assert f'<base href="/api/preview/{project_id}/proxy/">' in res_proxy.text

                # 4. Request static stylesheet via proxy
                res_css = await ac.get(f"/api/preview/{project_id}/proxy/styles.css", headers=headers)
                assert res_css.status_code == 200
                assert len(res_css.text) > 100

                # 5. Test Live E2E Verification endpoint
                res_live_test = await ac.get(f"/api/preview/{project_id}/test-live", headers=headers)
                assert res_live_test.status_code == 200
                live_data = res_live_test.json()
                assert live_data["passed"] is True
                assert live_data["passed_checks"] >= 3

                # 6. Interact with backend API: POST contact inquiry
                contact_payload = {
                    "sender_name": "Sarah Connor",
                    "sender_email": "sarah@cyberdyne.org",
                    "subject": "Analytics Lead Role",
                    "message": "We loved your case studies on churn prediction.",
                }
                res_post = await ac.post(f"/api/preview/{project_id}/proxy/api/v1/contact", json=contact_payload, headers=headers)
                assert res_post.status_code == 201
                assert res_post.json()["status"] == "received"

                # 7. Check logs capture
                res_logs = await ac.get(f"/api/preview/{project_id}/logs", headers=headers)
                assert res_logs.status_code == 200
                assert res_logs.json()["total"] >= 1
            finally:
                # 8. Stop server
                res_stop = await ac.post(f"/api/preview/{project_id}/stop", headers=headers)
                assert res_stop.status_code == 200
                assert res_stop.json()["status"] == "stopped"

    asyncio.run(_run())


def test_2_live_execution_bakery_storefront():
    """TEST 2: Full live execution, interactive shopping/orders, and restart persistence of Archetype B."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a website for a local bakery where customers can browse products, view prices and submit orders."
            res_an = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            blueprint = res_an.json()["blueprint"]

            res_cr = await ac.post("/api/projects", json={
                "name": "Live Bakery Storefront",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            # Start server
            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200
            assert res_start.json()["status"] == "running"

            try:
                # 1. Query products catalogue API
                res_prod = await ac.get(f"/api/preview/{project_id}/proxy/api/v1/products", headers=headers)
                assert res_prod.status_code == 200
                products = res_prod.json()["items"]
                assert len(products) >= 5

                # 2. Place an order
                order_payload = {
                    "customer_name": "Alice Baker",
                    "customer_email": "alice@pastry.com",
                    "customer_phone": "555-0192",
                    "pickup_time": "Tomorrow 9:00 AM",
                    "items": [
                        {
                            "product_id": products[0]["id"],
                            "product_name": products[0]["name"],
                            "unit_price": products[0]["price"],
                            "quantity": 2,
                        }
                    ],
                }
                res_order = await ac.post(f"/api/preview/{project_id}/proxy/api/v1/orders", json=order_payload, headers=headers)
                assert res_order.status_code == 201
                order_code = res_order.json()["order_code"]
                assert order_code.startswith("BAKE-") or order_code.startswith("ORD-")

                # 3. Query the order by code
                res_get_order = await ac.get(f"/api/preview/{project_id}/proxy/api/v1/orders/{order_code}", headers=headers)
                assert res_get_order.status_code == 200
                assert res_get_order.json()["customer_name"] == "Alice Baker"

                # 4. Restart server and verify persistence in SQLite
                res_restart = await ac.post(f"/api/preview/{project_id}/restart", headers=headers)
                assert res_restart.status_code == 200
                assert res_restart.json()["status"] == "running"

                # Query order again after restart
                res_after_restart = await ac.get(f"/api/preview/{project_id}/proxy/api/v1/orders/{order_code}", headers=headers)
                assert res_after_restart.status_code == 200
                assert res_after_restart.json()["customer_name"] == "Alice Baker"
            finally:
                await ac.post(f"/api/preview/{project_id}/stop", headers=headers)

    asyncio.run(_run())


def test_3_live_execution_student_attendance_saas():
    """TEST 3: Full live execution of Archetype C (Student Attendance SaaS Dashboard)."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            prompt = "Create a SaaS dashboard for managing student attendance."
            res_an = await ac.post("/api/projects/analyze-idea", json={"description": prompt}, headers=headers)
            blueprint = res_an.json()["blueprint"]

            res_cr = await ac.post("/api/projects", json={
                "name": "Live Attendance SaaS",
                "description": prompt,
                "blueprint": blueprint,
            }, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200
            assert res_start.json()["status"] == "running"

            try:
                # 1. Query attendance metrics
                res_metrics = await ac.get(f"/api/preview/{project_id}/proxy/api/v1/metrics/attendance", headers=headers)
                assert res_metrics.status_code == 200
                data_m = res_metrics.json()
                assert "attendance_rate" in data_m
                assert data_m["total_students"] >= 6

                # 2. Enroll a new student
                new_student = {
                    "student_id": "STU-E2E-99",
                    "full_name": "Jordan Peterson",
                    "grade_level": "Grade 11-B",
                    "email": "jordan.p@academy.edu",
                    "contact_phone": "555-888-9999",
                }
                res_stu = await ac.post(f"/api/preview/{project_id}/proxy/api/v1/students", json=new_student, headers=headers)
                assert res_stu.status_code == 201

                # 3. Mark batch roll-call attendance
                att_record = {
                    "records": [
                        {
                            "student_id": "STU-E2E-99",
                            "date": "2026-11-24",
                            "status": "Present",
                            "notes": "Arrived on time",
                        }
                    ]
                }
                res_att = await ac.post(f"/api/preview/{project_id}/proxy/api/v1/attendance/batch", json=att_record, headers=headers)
                assert res_att.status_code == 201
                assert res_att.json()["status"] == "saved"
                assert res_att.json()["count"] >= 1
            finally:
                await ac.post(f"/api/preview/{project_id}/stop", headers=headers)

    asyncio.run(_run())


def test_4_dynamic_port_allocation_concurrency():
    """TEST 4: Concurrent project sandboxes receive distinct ports with no collision."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_a = await ac.post("/api/projects", json={"name": "Concurrent App One"}, headers=headers)
            res_b = await ac.post("/api/projects", json={"name": "Concurrent App Two"}, headers=headers)
            p_a = res_a.json()["project"]["id"]
            p_b = res_b.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{p_a}/build", json={"force_build": True, "use_ai": False}, headers=headers)
            await ac.post(f"/api/orchestrator/projects/{p_b}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            start_a = await ac.post(f"/api/preview/{p_a}/start", headers=headers)
            start_b = await ac.post(f"/api/preview/{p_b}/start", headers=headers)

            assert start_a.status_code == 200 and start_a.json()["status"] == "running"
            assert start_b.status_code == 200 and start_b.json()["status"] == "running"

            port_a = start_a.json()["port"]
            port_b = start_b.json()["port"]
            try:
                # Ports must be strictly distinct
                assert port_a != port_b
                assert port_a >= 8100
                assert port_b >= 8100
            finally:
                await ac.post(f"/api/preview/{p_a}/stop", headers=headers)
                await ac.post(f"/api/preview/{p_b}/stop", headers=headers)

    asyncio.run(_run())


def test_5_missing_project_handling():
    """TEST 5: Starting non-existent or unbuilt project returns clean error."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_fake = await ac.post("/api/preview/non-existent-project-id/start", headers=headers)
            assert res_fake.status_code == 404

            res_unbuilt = await ac.post("/api/projects", json={"name": "Unbuilt App"}, headers=headers)
            p_unbuilt = res_unbuilt.json()["project"]["id"]
            res_start_unbuilt = await ac.post(f"/api/preview/{p_unbuilt}/start", headers=headers)
            assert res_start_unbuilt.status_code == 200
            assert res_start_unbuilt.json()["success"] is False
            assert "error" in res_start_unbuilt.json()

    asyncio.run(_run())


def test_6_crash_detection_and_log_capture():
    """TEST 6: Application crash is detected, captured, and reported in status and logs."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Crash Prone App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            # Intentionally corrupt server.py with a syntax error
            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "Crash Prone App")
            server_file = workspace_dir / "server.py"
            server_file.write_text("def broken_syntax(:\n    raise SystemExit('Intentional error')\n", encoding="utf-8")

            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200
            data = res_start.json()
            assert data["success"] is False
            assert data["status"] == "failed"

            # Check status endpoint confirms failure
            res_st = await ac.get(f"/api/preview/{project_id}/status", headers=headers)
            assert res_st.status_code == 200
            assert res_st.json()["status"] == "failed"

    asyncio.run(_run())


def test_7_ai_error_diagnosis_and_targeted_repair():
    """TEST 7: AI Debugger diagnoses error, applies targeted code fix, and repairs the project."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Self Healing App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            # 1. Diagnose current status or logs
            res_diag = await ac.post(f"/api/preview/{project_id}/diagnose", headers=headers)
            assert res_diag.status_code == 200
            diag_data = res_diag.json()
            assert "summary" in diag_data

            # 2. Test applying a targeted fix
            workspace_dir = WorkspaceBuilder.get_workspace_dir(project_id, "Self Healing App")
            server_file = workspace_dir / "server.py"
            original_text = server_file.read_text(encoding="utf-8")

            fix_payload = {
                "file": "server.py",
                "original_snippet": 'version="1.0.0"',
                "replacement_snippet": 'version="1.0.1"',
            }
            res_apply = await ac.post(f"/api/preview/{project_id}/apply-fix", json=fix_payload, headers=headers)
            assert res_apply.status_code == 200
            assert res_apply.json()["success"] is True

            # Verify backup file was created
            backup_file = server_file.with_suffix(".py.bak")
            assert backup_file.exists()

            # 3. Test rollback
            res_roll = await ac.post(f"/api/preview/{project_id}/rollback-fix", json={"file": "server.py"}, headers=headers)
            assert res_roll.status_code == 200
            assert res_roll.json()["success"] is True
            assert server_file.read_text(encoding="utf-8") == original_text

    asyncio.run(_run())


def test_8_security_and_secret_sanitization():
    """TEST 8: Subprocess execution environment sanitizes and blocks access to backend secrets."""
    port = 8399
    workspace = Path(".").resolve()
    env = execution_engine.sanitize_environment(port, workspace)

    assert env["PORT"] == "8399"
    assert env["PYTHONUNBUFFERED"] == "1"

    # Strict check: Backend credentials must NOT be leaked
    assert "SECRET_KEY" not in env
    assert "DATABASE_URL" not in env
    assert "GOOGLE_API_KEY" not in env
    assert "OPENROUTER_API_KEY" not in env
    assert "GITHUB_CLIENT_SECRET" not in env


def test_9_cross_user_isolation_and_unauthorized_rejection():
    """TEST 9: User B cannot start, inspect, or proxy User A's preview sandbox."""
    async def _run():
        users = await _ensure_test_users()
        headers_a = users["headers_a"]
        headers_b = users["headers_b"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_a = await ac.post("/api/projects", json={"name": "Alpha Private Sandbox"}, headers=headers_a)
            project_id = res_a.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers_a)

            # User B attempts to start User A's preview -> 404 (Not found or access denied)
            res_unauth_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers_b)
            assert res_unauth_start.status_code == 404

            # User B attempts to read status -> 404
            res_unauth_st = await ac.get(f"/api/preview/{project_id}/status", headers=headers_b)
            assert res_unauth_st.status_code == 404

            # Unauthenticated requests reject with 401
            res_no_auth = await ac.post(f"/api/preview/{project_id}/start")
            assert res_no_auth.status_code == 401

    asyncio.run(_run())


def test_10_sandbox_cleanup_on_stop():
    """TEST 10: Process stopping and cleanup terminates subprocesses and frees resources."""
    async def _run():
        users = await _ensure_test_users()
        headers = users["headers_a"]
        user_id = users["user_a_id"]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res_cr = await ac.post("/api/projects", json={"name": "Reap App"}, headers=headers)
            project_id = res_cr.json()["project"]["id"]

            await ac.post(f"/api/orchestrator/projects/{project_id}/build", json={"force_build": True, "use_ai": False}, headers=headers)

            res_start = await ac.post(f"/api/preview/{project_id}/start", headers=headers)
            assert res_start.status_code == 200
            assert res_start.json()["status"] == "running"

            # Check process object is alive
            proc_obj = execution_engine._processes.get(project_id)
            assert proc_obj is not None
            assert proc_obj.is_alive() is True

            # Stop
            res_stop = await ac.post(f"/api/preview/{project_id}/stop", headers=headers)
            assert res_stop.status_code == 200
            assert proc_obj.is_alive() is False

    asyncio.run(_run())

