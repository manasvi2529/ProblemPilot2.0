"""
Targeted Tests: Live Preview Entry Point Detection & Multi-Runtime Execution.

Covers:
1. HTML-only generated project (index.html -> static HTTP server).
2. Python generic application (main.py -> python generic runner).
3. FastAPI application (server.py with FastAPI instance -> uvicorn stem:app).
4. React/Next.js application (package.json with dev/start scripts -> npm command).
5. Missing entry point -> clear diagnostic message identifying checked runtimes and files.
6. Invalid package.json -> fallback with informative warning and error report.
7. Successful preview startup, health check probe, and port allocation.
8. Process termination and sandbox cleanup guarantee.
"""
import sys
import json
import asyncio
import pytest
from pathlib import Path
from unittest import mock
from backend.config import settings

from backend.services.execution_engine import ExecutionEngine, ProjectProcess


class TestPreviewEntryPointDetection:
    """Tests ExecutionEngine entry point detection and runtime command determination."""

    def test_html_only_project_detection_and_command(self, tmp_path):
        """1. HTML-only project detects index.html and generates python http.server command."""
        (tmp_path / "index.html").write_text("<!DOCTYPE html><html><body>Test</body></html>", encoding="utf-8")
        (tmp_path / "styles.css").write_text("body { color: red; }", encoding="utf-8")

        entry_point = ExecutionEngine.detect_entry_point(tmp_path)
        assert entry_point == "index.html"

        cmd, runtime_type = ExecutionEngine.determine_runtime_command(tmp_path, entry_point, 8550)
        assert runtime_type == "static_http"
        assert sys.executable in cmd
        assert "-m" in cmd
        assert "http.server" in cmd
        assert "8550" in cmd

    def test_python_generic_application_detection_and_command(self, tmp_path):
        """2. Python script with main block detects app.py and runs directly."""
        (tmp_path / "app.py").write_text(
            "import time\nif __name__ == '__main__':\n    print('Running generic app')\n",
            encoding="utf-8",
        )

        entry_point = ExecutionEngine.detect_entry_point(tmp_path)
        assert entry_point == "app.py"

        cmd, runtime_type = ExecutionEngine.determine_runtime_command(tmp_path, entry_point, 8551)
        assert runtime_type == "python_generic"
        assert cmd == [sys.executable, "app.py"]

    def test_fastapi_application_detection_and_command(self, tmp_path):
        """3. FastAPI application detects server.py and generates uvicorn command with app instance."""
        (tmp_path / "server.py").write_text(
            "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/api/v1/health')\ndef h(): return {'status': 'ok'}\n",
            encoding="utf-8",
        )

        entry_point = ExecutionEngine.detect_entry_point(tmp_path)
        assert entry_point == "server.py"

        cmd, runtime_type = ExecutionEngine.determine_runtime_command(tmp_path, entry_point, 8552)
        assert runtime_type == "fastapi"
        assert "-m" in cmd
        assert "uvicorn" in cmd
        assert "server:app" in cmd
        assert "8552" in cmd

    def test_react_nextjs_package_json_detection_and_command(self, tmp_path):
        """4. React/Next.js application detects package.json and configures npm run dev."""
        pkg = {
            "name": "sample-react-app",
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
            },
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        entry_point = ExecutionEngine.detect_entry_point(tmp_path)
        assert entry_point == "package.json"

        cmd, runtime_type = ExecutionEngine.determine_runtime_command(tmp_path, entry_point, 8553)
        assert runtime_type == "node"
        assert "run" in cmd
        assert "dev" in cmd

    @pytest.mark.asyncio
    async def test_missing_entry_point_returns_clear_diagnostics(self, tmp_path):
        """5. Missing entry point with non-code files returns clear diagnostic listing checked runtimes and files."""
        (tmp_path / "random_notes.txt").write_text("not a code file", encoding="utf-8")
        (tmp_path / "data.csv").write_text("a,b,c", encoding="utf-8")

        entry_point = ExecutionEngine.detect_entry_point(tmp_path)
        assert entry_point is None

        engine = ExecutionEngine()
        res = await engine.start_project("proj_missing_ep", "user_test", tmp_path)

        assert res["success"] is False
        assert res["status"] == "failed"
        assert "No runnable entry point found" in res["error"]
        assert "FastAPI/ASGI" in res["error"]
        assert "Static Web" in res["error"]
        assert "random_notes.txt" in str(res["diagnostics"]["files_present"])

    @pytest.mark.asyncio
    async def test_empty_workspace_returns_lifecycle_not_started_error(self, tmp_path):
        """8. Empty workspace returns not_started with Build stage guidance."""
        engine = ExecutionEngine()
        res = await engine.start_project("proj_empty_ep", "user_test", tmp_path)
        assert res["success"] is False
        assert res["status"] == "not_started"
        assert res["not_built"] is True
        assert "Your application has not been built yet. Complete the Build stage before starting Preview." in res["error"]

    def test_invalid_package_json_fallback(self, tmp_path):
        """6. Malformed package.json handles errors gracefully without crashing."""
        (tmp_path / "package.json").write_text("{ broken json, missing closing brace", encoding="utf-8")

        entry_point = ExecutionEngine.detect_entry_point(tmp_path)
        assert entry_point == "package.json"

        cmd, runtime_type = ExecutionEngine.determine_runtime_command(tmp_path, entry_point, 8554)
        assert runtime_type == "node"
        assert "start" in cmd

    @pytest.mark.asyncio
    async def test_live_preview_static_html_startup_health_and_cleanup(self, tmp_path):
        """7 & 8. Actual startup of static HTML project, port binding, and guaranteed process cleanup.
        Bounded: Startup 30s, health check 10s, overall test 60s.
        """
        orig_fallback = settings.ALLOW_INSECURE_LOCAL_FALLBACK
        settings.ALLOW_INSECURE_LOCAL_FALLBACK = True

        try:
            async with asyncio.timeout(60.0):
                (tmp_path / "index.html").write_text(
                    "<!DOCTYPE html><html><head><title>Preview Live</title></head><body><h1>Hello World</h1></body></html>",
                    encoding="utf-8",
                )

                engine = ExecutionEngine()
                project_id = "test_live_html_proj_001"
                user_id = "test_user_001"

                try:
                    start_res = await engine.start_project(
                        project_id=project_id,
                        user_id=user_id,
                        workspace_dir=tmp_path,
                        timeout_seconds=30.0,
                    )

                    assert start_res["success"] is True
                    assert start_res["status"] == "running"
                    assert "port" in start_res
                    port = start_res["port"]

                    # Verify HTTP health / root reachability with bounded 10s timeout
                    import httpx
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        res = await client.get(f"http://127.0.0.1:{port}/")
                        assert res.status_code == 200
                        assert "Hello World" in res.text

                finally:
                    # 8. Guaranteed cleanup test
                    stop_res = engine.stop_project(project_id, user_id)
                    assert stop_res["success"] is True
                    assert stop_res["status"] == "stopped"

                    status_res = await engine.get_project_status(project_id, user_id)
                    assert status_res["running"] is False
        finally:
            settings.ALLOW_INSECURE_LOCAL_FALLBACK = orig_fallback
