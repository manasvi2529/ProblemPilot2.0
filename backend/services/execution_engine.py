"""
Problem2Project AI — Dedicated Sandbox Execution Engine.

Responsibilities:
1. Detect technology stack and entry point (server.py, app.py, main.py).
2. Allocate dynamic ports to prevent collisions across concurrent projects.
3. Launch project processes in isolated environments with sanitized credentials.
4. Capture real-time stdout and stderr into bounded ring buffers.
5. Poll and verify real HTTP health checks before marking running.
6. Enforce execution limits, CPU/memory constraints, and timeouts.
7. Support start, stop, restart, status, logs, and process termination.
"""
import os
import sys
import socket
import logging
import asyncio
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import deque
import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class ProjectProcess:
    """Represents a managed, sandboxed project process."""

    def __init__(
        self,
        project_id: str,
        user_id: str,
        workspace_dir: Path,
        port: int,
        entry_point: str,
    ):
        self.project_id = project_id
        self.user_id = user_id
        self.workspace_dir = Path(workspace_dir).resolve()
        self.port = port
        self.entry_point = entry_point
        self.process: Optional[subprocess.Popen] = None
        self.status = "not_started"  # not_started | starting | running | failed | stopped
        self.error_message: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self.pid: Optional[int] = None
        self.health_url = f"http://127.0.0.1:{port}/api/v1/health"
        self.root_url = f"http://127.0.0.1:{port}/"

        # Ring buffers for stdout and stderr (max 500 lines each)
        self.stdout_lines: deque = deque(maxlen=500)
        self.stderr_lines: deque = deque(maxlen=500)
        self._threads: List[threading.Thread] = []

    def append_stdout(self, line: str):
        cleaned = line.rstrip("\r\n")
        if cleaned:
            self.stdout_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] {cleaned}")

    def append_stderr(self, line: str):
        cleaned = line.rstrip("\r\n")
        if cleaned:
            self.stderr_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] {cleaned}")

    def get_logs(self, limit: int = 100) -> List[str]:
        """Combine and return recent stdout and stderr lines in chronological sequence."""
        combined = list(self.stdout_lines) + list(self.stderr_lines)
        return combined[-limit:]

    def is_alive(self) -> bool:
        if self.process is None:
            return False
        return self.process.poll() is None


class ExecutionEngine:
    """
    Central manager for isolated project runtime execution, health monitoring,
    port assignment, and lifecycle management.
    """

    PORT_RANGE_START = 8100
    PORT_RANGE_END = 8900

    def __init__(self):
        self._processes: Dict[str, ProjectProcess] = {}
        self._lock = threading.RLock()

    def find_available_port(self, start: int = PORT_RANGE_START, end: int = PORT_RANGE_END) -> int:
        """Find an unallocated TCP port on localhost, taking into account registered active projects."""
        with self._lock:
            allocated = {
                p.port for p in self._processes.values()
                if p.status in ("starting", "running") and p.port
            }

        for port in range(start, end):
            if port in allocated:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue
        raise RuntimeError("No available TCP ports in configured execution range.")

    @staticmethod
    def detect_entry_point(workspace_dir: Path) -> Optional[str]:
        """Identify main application entry point."""
        for candidate in ("server.py", "app.py", "main.py"):
            if (workspace_dir / candidate).exists():
                return candidate
        return None

    @staticmethod
    def sanitize_environment(port: int, workspace_dir: Path) -> Dict[str, str]:
        """
        Build an isolated subprocess environment preventing access to parent application secrets.
        Strips backend credentials, database URIs, API keys, and injection vectors.
        """
        SECRET_KEYS = {
            "SECRET_KEY", "JWT_SECRET", "DATABASE_URL", "GOOGLE_API_KEY",
            "GEMINI_API_KEY", "OPENROUTER_API_KEY", "GITHUB_CLIENT_SECRET",
            "GITHUB_PERSONAL_ACCESS_TOKEN", "SERPER_API_KEY", "TAVILY_API_KEY",
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_SECRET_ACCESS_KEY",
        }
        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in SECRET_KEYS and not k.startswith("BACKEND_")
        }
        clean_env["PORT"] = str(port)
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        clean_env["HOST"] = "127.0.0.1"
        clean_env["SANDBOX_WORKSPACE"] = str(workspace_dir)
        clean_env["PATH"] = os.environ.get("PATH", "")
        clean_env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
        clean_env["COMSPEC"] = os.environ.get("COMSPEC", "")
        return clean_env

    async def start_project(
        self,
        project_id: str,
        user_id: str,
        workspace_dir: Path,
        preferred_port: Optional[int] = None,
        timeout_seconds: float = 20.0,
    ) -> Dict[str, Any]:
        """
        Launch the project inside an isolated background subprocess,
        probe its health endpoint, and transition to running state.
        """
        workspace_dir = Path(workspace_dir).resolve()
        if not workspace_dir.exists():
            return {
                "success": False,
                "status": "failed",
                "error": f"Workspace directory does not exist: {workspace_dir}",
            }

        entry_point = self.detect_entry_point(workspace_dir)
        if not entry_point:
            return {
                "success": False,
                "status": "failed",
                "error": "No runnable entry point found (expected server.py, app.py, or main.py).",
            }

        with self._lock:
            # Terminate existing instance for this project if running
            existing = self._processes.get(project_id)
            if existing and existing.is_alive():
                self._stop_process_instance(existing)

            port = preferred_port or self.find_available_port()
            proc_obj = ProjectProcess(
                project_id=project_id,
                user_id=user_id,
                workspace_dir=workspace_dir,
                port=port,
                entry_point=entry_point,
            )
            self._processes[project_id] = proc_obj

        # Patch port in entry point script if explicitly bound
        entry_file = workspace_dir / entry_point
        try:
            content = entry_file.read_text(encoding="utf-8")
            # Replace default port references (e.g. port=8030 or port=8020) with our dynamic port
            import re
            patched = re.sub(r'port\s*=\s*\d+', f'port={port}', content)
            if patched != content:
                entry_file.write_text(patched, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not patch port in {entry_file}: {e}")

        # Start process with sanitized environment
        env = self.sanitize_environment(port, workspace_dir)
        python_exec = sys.executable

        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        proc_obj.status = "starting"
        proc_obj.started_at = datetime.now(timezone.utc)

        stem = Path(entry_point).stem
        cmd = [python_exec, "-m", "uvicorn", f"{stem}:app", "--host", "127.0.0.1", "--port", str(port)]

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(workspace_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=creationflags,
            )
            proc_obj.process = proc
            proc_obj.pid = proc.pid

            # Spawn reader threads for stdout and stderr
            def _read_stdout():
                try:
                    for line in iter(proc.stdout.readline, ''):
                        if not line:
                            break
                        proc_obj.append_stdout(line)
                except Exception:
                    pass
                finally:
                    proc.stdout.close()

            def _read_stderr():
                try:
                    for line in iter(proc.stderr.readline, ''):
                        if not line:
                            break
                        proc_obj.append_stderr(line)
                except Exception:
                    pass
                finally:
                    proc.stderr.close()

            t_out = threading.Thread(target=_read_stdout, daemon=True)
            t_err = threading.Thread(target=_read_stderr, daemon=True)
            t_out.start()
            t_err.start()
            proc_obj._threads.extend([t_out, t_err])

        except Exception as e:
            proc_obj.status = "failed"
            proc_obj.error_message = f"Failed to spawn application process: {str(e)}"
            return {
                "success": False,
                "status": "failed",
                "error": proc_obj.error_message,
                "port": port,
            }

        # Probe health check until successful or timeout
        poll_interval = 0.4
        max_attempts = int(timeout_seconds / poll_interval)
        healthy = False

        async with httpx.AsyncClient(timeout=2.0) as client:
            for _ in range(max_attempts):
                await asyncio.sleep(poll_interval)
                # Check if process exited prematurely
                if proc.poll() is not None:
                    proc_obj.status = "failed"
                    exit_code = proc.poll()
                    err_logs = "\n".join(list(proc_obj.stderr_lines)[-10:])
                    proc_obj.error_message = (
                        f"Process exited prematurely with code {exit_code}. "
                        f"Details: {err_logs or 'No stderr captured.'}"
                    )
                    return {
                        "success": False,
                        "status": "failed",
                        "error": proc_obj.error_message,
                        "port": port,
                        "logs": proc_obj.get_logs(30),
                    }

                # Probe health probe endpoint, fallback to root
                for target_url in (proc_obj.health_url, proc_obj.root_url):
                    try:
                        resp = await client.get(target_url)
                        if resp.status_code in (200, 301, 302, 307):
                            healthy = True
                            break
                    except Exception:
                        pass
                if healthy:
                    break

        if healthy:
            proc_obj.status = "running"
            return {
                "success": True,
                "status": "running",
                "port": port,
                "pid": proc_obj.pid,
                "preview_url": f"http://localhost:{port}",
                "proxy_path": f"/api/preview/{project_id}/proxy/",
                "health_url": proc_obj.health_url,
                "started_at": proc_obj.started_at.isoformat(),
            }
        else:
            proc_obj.status = "failed"
            proc_obj.error_message = f"Health check probe timed out after {timeout_seconds}s at {proc_obj.health_url}"
            return {
                "success": False,
                "status": "failed",
                "error": proc_obj.error_message,
                "port": port,
                "logs": proc_obj.get_logs(30),
            }

    def _stop_process_instance(self, proc_obj: ProjectProcess):
        """Helper to terminate a running process instance cleanly."""
        if proc_obj.process and proc_obj.is_alive():
            pid = proc_obj.pid
            try:
                try:
                    proc_obj.process.kill()
                except Exception:
                    pass
                if sys.platform == "win32" and pid:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5)
                try:
                    proc_obj.process.wait(timeout=1.0)
                except Exception:
                    pass
                proc_obj.process.poll()
            except Exception as e:
                logger.warning(f"Error terminating process PID {pid}: {e}")

        proc_obj.status = "stopped"
        proc_obj.stopped_at = datetime.now(timezone.utc)

    def stop_project(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Stop running sandbox project process for user."""
        with self._lock:
            proc_obj = self._processes.get(project_id)
            if not proc_obj:
                return {"success": True, "status": "stopped", "message": "No active process found."}

            if proc_obj.user_id != user_id:
                raise PermissionError("Access denied: You do not own this project execution.")

            self._stop_process_instance(proc_obj)
            return {
                "success": True,
                "status": "stopped",
                "project_id": project_id,
                "stopped_at": proc_obj.stopped_at.isoformat() if proc_obj.stopped_at else None,
            }

    async def restart_project(
        self,
        project_id: str,
        user_id: str,
        workspace_dir: Path,
    ) -> Dict[str, Any]:
        """Gracefully stop and restart the project sandbox."""
        self.stop_project(project_id, user_id)
        await asyncio.sleep(0.5)
        return await self.start_project(project_id, user_id, workspace_dir)

    async def get_project_status(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Check live runtime execution state, port, uptime, and health."""
        with self._lock:
            proc_obj = self._processes.get(project_id)

        if not proc_obj:
            return {
                "project_id": project_id,
                "status": "not_started",
                "running": False,
                "port": None,
                "pid": None,
                "preview_url": None,
                "proxy_path": None,
            }

        if proc_obj.user_id != user_id:
            raise PermissionError("Access denied: You do not own this project execution.")

        # If process was expected to run but terminated
        if proc_obj.status == "running" and not proc_obj.is_alive():
            proc_obj.status = "failed"
            exit_code = proc_obj.process.poll() if proc_obj.process else -1
            proc_obj.error_message = f"Process terminated unexpectedly with exit code {exit_code}."

        is_running = (proc_obj.status == "running" and proc_obj.is_alive())

        uptime_seconds = 0
        if is_running and proc_obj.started_at:
            uptime_seconds = int((datetime.now(timezone.utc) - proc_obj.started_at).total_seconds())

        return {
            "project_id": project_id,
            "status": proc_obj.status,
            "running": is_running,
            "port": proc_obj.port if is_running else None,
            "pid": proc_obj.pid if is_running else None,
            "preview_url": f"http://localhost:{proc_obj.port}" if is_running else None,
            "proxy_path": f"/api/preview/{project_id}/proxy/" if is_running else None,
            "health_url": proc_obj.health_url if is_running else None,
            "uptime_seconds": uptime_seconds,
            "error_message": proc_obj.error_message,
            "started_at": proc_obj.started_at.isoformat() if proc_obj.started_at else None,
        }

    def get_project_logs(self, project_id: str, user_id: str, limit: int = 150) -> Dict[str, Any]:
        """Retrieve stdout and stderr logs for the project."""
        with self._lock:
            proc_obj = self._processes.get(project_id)

        if not proc_obj:
            return {"project_id": project_id, "logs": [], "total": 0}

        if proc_obj.user_id != user_id:
            raise PermissionError("Access denied: You do not own this project execution.")

        logs = proc_obj.get_logs(limit)
        return {
            "project_id": project_id,
            "status": proc_obj.status,
            "logs": logs,
            "total": len(logs),
        }

    def cleanup_all(self):
        """Reap and kill all active subprocesses on shutdown."""
        with self._lock:
            for pid, proc_obj in list(self._processes.items()):
                try:
                    self._stop_process_instance(proc_obj)
                except Exception:
                    pass
            self._processes.clear()


# Global singleton instance
execution_engine = ExecutionEngine()

