#!/usr/bin/env python3
"""
ProblemPilot AI — Master Process Runner
Launches both the FastAPI backend (port 8000) and Next.js frontend (port 3000) concurrently.
Handles clean shutdown of both processes upon Ctrl+C.
"""
import os
import sys
import time
import signal
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"

# Detect Python interpreter (prefer virtualenv if present)
VENV_PYTHON = ROOT_DIR / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    PYTHON_EXE = sys.executable
else:
    PYTHON_EXE = str(VENV_PYTHON)

# Detect npm executable on Windows
NPM_CMD = "npm.cmd" if sys.platform == "win32" else "npm"


def main():
    print("=" * 65)
    print("   ProblemPilot AI — Launching Full-Stack Services")
    print("=" * 65)
    print(f"[*] Root Directory : {ROOT_DIR}")
    print(f"[*] Web Directory  : {WEB_DIR}")
    print(f"[*] Python Runtime : {PYTHON_EXE}")
    print(f"[*] Backend URL    : http://127.0.0.1:8000")
    print(f"[*] Frontend URL   : http://localhost:3000")
    print("=" * 65)

    backend_proc = None
    frontend_proc = None

    try:
        # 1. Start FastAPI Backend
        print("\n[1/2] Starting FastAPI Backend on port 8000...")
        backend_cmd = [
            PYTHON_EXE,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--reload",
        ]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(ROOT_DIR),
            env=os.environ.copy(),
        )
        print("  -> FastAPI process started (PID: {})".format(backend_proc.pid))

        # Give backend a moment to bind socket
        time.sleep(1.5)

        # 2. Start Next.js Frontend
        print("\n[2/2] Starting Next.js Frontend on port 3000...")
        frontend_cmd = [NPM_CMD, "run", "dev"]
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(WEB_DIR),
            env=os.environ.copy(),
        )
        print("  -> Next.js dev server started (PID: {})".format(frontend_proc.pid))

        print("\n" + "=" * 65)
        print("   Both services are now running live!")
        print("   Open your browser to: http://localhost:3000")
        print("   (FastAPI Reverse Proxy forwards /api requests to :8000)")
        print("   Press Ctrl+C to terminate both servers.")
        print("=" * 65 + "\n")

        # Keep parent alive and monitor child processes
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print(f"[!] Backend process exited with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"[!] Frontend process exited with code {frontend_proc.returncode}")
                break

    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received (Ctrl+C). Terminating processes...")
    finally:
        # Graceful cleanup
        if backend_proc and backend_proc.poll() is None:
            print("[*] Stopping FastAPI backend...")
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                backend_proc.kill()

        if frontend_proc and frontend_proc.poll() is None:
            print("[*] Stopping Next.js frontend...")
            frontend_proc.terminate()
            try:
                frontend_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                frontend_proc.kill()

        print("[OK] All processes terminated successfully.")


if __name__ == "__main__":
    main()
