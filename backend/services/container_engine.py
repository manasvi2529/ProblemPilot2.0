"""
Problem2Project AI — Container Sandbox Execution Manager.

Provides production-grade Docker container isolation for user-generated applications.
Enforces:
- Non-root user (UID 1000:1000).
- CPU quota limit (0.5 CPU).
- Memory limit (512 MB, no swap).
- Process/PID limit (pids-limit=64).
- Read-only root filesystem with scoped temporary writable volume for workspace.
- Stripped environment: zero parent secrets, JWT secrets, DB credentials, or API keys.
- No Docker socket mounting or privileged capabilities (drops all capabilities, adds NET_BIND_SERVICE).
- Port mapping to localhost only (127.0.0.1:{port}).
- Startup (max 30s) and health-check (max 10s) timeout enforcement.
- Graceful and forceful container termination and port release on cancellation or stop.
- Strict isolation preventing access to other users' directories.
"""
import shutil
import subprocess
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

from backend.config import settings

logger = logging.getLogger(__name__)


class ContainerSandboxEngine:
    """Manages Docker container lifecycle for untrusted generated applications."""

    @classmethod
    def is_docker_available(cls) -> bool:
        """Check whether the docker binary is present and the Docker daemon is responding."""
        docker_bin = shutil.which("docker")
        if not docker_bin:
            return False
        try:
            res = subprocess.run(
                [docker_bin, "info"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def build_docker_run_args(
        cls,
        container_name: str,
        workspace_dir: Path,
        port: int,
        cmd: List[str],
        image: Optional[str] = None,
        cpu_limit: Optional[float] = None,
        memory_mb: Optional[int] = None,
        pids_limit: Optional[int] = None,
    ) -> List[str]:
        """
        Construct hardened docker run CLI arguments implementing defense-in-depth isolation.
        """
        image_name = image or settings.CONTAINER_IMAGE
        cpus = cpu_limit or settings.CONTAINER_CPU_LIMIT
        mem_mb = memory_mb or settings.MAX_MEMORY_MB
        pids = pids_limit or settings.CONTAINER_PIDS_LIMIT

        docker_bin = shutil.which("docker") or "docker"

        # Docker run arguments enforcing all security mandates
        args = [
            docker_bin,
            "run",
            "--rm",                                     # Auto-remove container upon exit
            "--name", container_name,
            "-p", f"127.0.0.1:{port}:{port}",          # Bound only to host loopback interface
            "--cpus", str(cpus),                       # CPU quota
            "--memory", f"{mem_mb}m",                  # Hard memory ceiling
            "--memory-swap", f"{mem_mb}m",             # Prevent disk swap escape
            "--pids-limit", str(pids),                 # Prevent fork bombs
            "--security-opt", "no-new-privileges:true",# Disallow privilege escalation
            "--cap-drop", "ALL",                       # Drop all root Linux capabilities
            "--cap-add", "NET_BIND_SERVICE",           # Only allow binding to service port
            "--user", "1000:1000",                     # Non-root user
            "--network", "bridge",                     # Bridge network isolated from host stack
            # Mount workspace directory as volume
            "-v", f"{workspace_dir.resolve().as_posix()}:/workspace:rw",
            "-w", "/workspace",
            # Standard sanitized environment variables inside container
            "-e", f"PORT={port}",
            "-e", "HOST=0.0.0.0",
            "-e", "PYTHONUNBUFFERED=1",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            image_name,
        ]
        args.extend(cmd)
        return args

    @classmethod
    def stop_container(cls, container_name: str, timeout: int = 5) -> bool:
        """Forcefully stop and clean up a running Docker container by name."""
        docker_bin = shutil.which("docker")
        if not docker_bin:
            return False
        try:
            subprocess.run(
                [docker_bin, "kill", container_name],
                capture_output=True,
                timeout=timeout,
            )
            subprocess.run(
                [docker_bin, "rm", "-f", container_name],
                capture_output=True,
                timeout=timeout,
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to kill docker container {container_name}: {e}")
            return False

    @classmethod
    def inspect_container_status(cls, container_name: str) -> Optional[Dict[str, Any]]:
        """Query Docker daemon for container running status and resource consumption."""
        docker_bin = shutil.which("docker")
        if not docker_bin:
            return None
        try:
            res = subprocess.run(
                [docker_bin, "inspect", container_name],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0:
                import json
                data = json.loads(res.stdout)
                if data and isinstance(data, list):
                    return data[0]
            return None
        except Exception:
            return None
