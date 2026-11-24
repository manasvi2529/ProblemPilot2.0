"""
ProblemPilot AI — Workspace Builder, Isolated Runner & Debugger
Generates full-stack source code inside dedicated project sandbox directories,
executes automated verification tests in isolated environments,
and performs bounded diagnostic repairs.
"""
import os
import sys
import re
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import settings
from backend.models.project import Project, ProjectFile
from backend.services.research_service import analyze_with_ai, extract_json_from_llm
from backend.services.website_generator import WebsiteGenerator

logger = logging.getLogger(__name__)


class WorkspaceBuilder:
    """
    Builds real, working full-stack applications in sandboxed project workspaces.
    """

    @staticmethod
    def get_workspace_dir(project_id: str, project_name: str = "") -> Path:
        """Get or locate the isolated project workspace directory."""
        clean_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in (project_name or project_id)).lower()
        
        # 1. Check if legacy unsuffixed directory exists (e.g. data/sandboxes/top_10_ai_app_development)
        legacy_dir = settings.SANDBOX_DIR / clean_name
        if legacy_dir.exists() and any(legacy_dir.iterdir()):
            return legacy_dir.resolve()

        # 2. Check if suffixed directory exists
        dir_name = f"{clean_name[:40]}_{project_id[:8]}"
        workspace = settings.SANDBOX_DIR / dir_name
        if workspace.exists():
            return workspace.resolve()

        # 3. Create suffixed directory by default
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace.resolve()

    @staticmethod
    def generate_project_source_files(
        project_name: str,
        blueprint: Dict[str, Any],
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate complete, functioning full-stack codebase matching the blueprint.
        Delegates to WebsiteGenerator to synthesize real, distinct, production-grade applications.
        """
        return WebsiteGenerator.generate_codebase(
            project_name=project_name,
            blueprint=blueprint,
            custom_instructions=custom_instructions,
        )

    @classmethod
    async def generate_project_source_files_with_ai(
        cls,
        project_name: str,
        blueprint: Dict[str, Any],
        tech_stack: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate complete, fully customized production source code using AI LLM.
        Directly translates the project blueprint, database schema, API contracts,
        and custom tech stack into real, functioning files.
        Falls back to dynamic blueprint template generator if AI is not configured or errors.
        """
        if not settings.ai_configured:
            logger.info("AI provider not configured, falling back to blueprint code synthesizer.")
            return cls.generate_project_source_files(project_name, blueprint)

        clean_title = (project_name or "Autonomous System").replace("'", "").strip()
        desc = blueprint.get("detailed_context", blueprint.get("problem_statement", "")).strip()
        stack = tech_stack or blueprint.get("tech_stack", {})
        db_schema = blueprint.get("database_schema", [])
        api_endpoints = blueprint.get("api_endpoints", blueprint.get("api_contracts", []))
        features = blueprint.get("mvp_features", [])

        schema_str = json.dumps(db_schema, indent=2) if db_schema else "Standard entities table with id, title, status, created_at"
        api_str = json.dumps(api_endpoints, indent=2) if api_endpoints else "REST CRUD endpoints: /api/v1/health, /api/v1/entities"
        stack_str = json.dumps(stack, indent=2) if stack else "Frontend: HTML5/CSS3/Vanilla JS, Backend: FastAPI, Database: SQLite/PostgreSQL"
        features_str = "\n".join(f"- {f}" for f in features) if features else "- Complete domain CRUD operations\n- Automated anomaly detection\n- Telemetry dashboard"

        custom_prompt_text = f"\nSpecific User Requirements / Custom Features:\n{custom_instructions}\n" if custom_instructions else ""

        system_prompt = (
            "You are a Principal Software Engineer and Full-Stack Architect. "
            "You write real, complete, bug-free, production-grade code without placeholders, "
            "TODOs, or omitted sections. You output ONLY valid JSON mapping filenames to file contents."
        )

        prompt = f"""Generate a complete, fully functioning, modular, production-ready software codebase tailored specifically for this project:

Project Name: {clean_title}
Problem Description: {desc}
Core Features:
{features_str}

Tech Stack:
{stack_str}

Database Schema:
{schema_str}

API Contracts:
{api_str}
{custom_prompt_text}
CRITICAL ARCHITECTURE & CODE GENERATION REQUIREMENTS:
1. Generate complete, non-stubbed source code for a production modular application matching the tech stack.
   You should generate a rich set of files (typically 10-15 files) including:
   - "server.py": Executable application entrypoint with CORS, route mounting, and static files.
   - "models.py": Pydantic V2 domain models & schemas matching the database schema.
   - "database.py": Database engine / session management with seed data.
   - "routes_entities.py": Modular CRUD router implementing business operations.
   - "index.html": Modern responsive dashboard with dark glassmorphic UI, statistics summary cards, search filter input, dynamic table for entities, modal dialog to create new records, and toast notifications.
   - "styles.css": Polished dark-mode CSS with glassmorphism (backdrop-filter: blur), tactile micro-interactions (:active {{ transform: scale(0.97); transition: transform 140ms ease-out; }}), CSS variables, clean typography, responsive layout, and status indicators.
   - "app.js": Complete vanilla ES6 JavaScript connecting to backend at /api/v1/entities, fetching records on load, modal form creation, deletion, instant search filtering, and updating status counters.
   - "test_suite.py": Complete executable pytest test suite using fastapi.testclient.TestClient testing /api/v1/health, /api/v1/metrics/summary, and the entity CRUD lifecycle.
   - "requirements.txt": Exact Python dependencies: fastapi>=0.115.0, uvicorn>=0.30.0, pydantic>=2.7.0, httpx>=0.27.0, pytest>=8.0.0, pytest-asyncio>=0.23.0.
   - "Dockerfile": Multi-stage production container specification.
   - "docker-compose.yml": Local development container orchestration.
   - ".env.example": Configurable environment template.
   - "README.md": Comprehensive documentation including Architecture, Tech Stack, Running Locally, and Verification Tests.
   - ".gitignore": Python, cache, and virtual environment ignore patterns.
   - "vercel.json": Cloud deployment configuration.
   If the tech stack or custom instructions require additional files (e.g. Next.js components, SQL scripts, worker scripts), include them too!

2. FORMAT RULE:
Output a single valid JSON object where keys are the relative file paths and values are the complete file content strings:
{{
  "index.html": "<!DOCTYPE html>...",
  "styles.css": "...",
  "app.js": "...",
  "server.py": "...",
  "models.py": "...",
  "database.py": "...",
  "routes_entities.py": "...",
  "test_suite.py": "...",
  "requirements.txt": "...",
  "Dockerfile": "...",
  "docker-compose.yml": "...",
  ".env.example": "...",
  "README.md": "...",
  ".gitignore": "...",
  "vercel.json": "..."
}}
Return ONLY the raw JSON object. No explanations outside JSON."""

        try:
            logger.info(f"Synthesizing full codebase for '{clean_title}' using AI...")
            ai_res = await analyze_with_ai(prompt, system_prompt=system_prompt, temperature=0.2)
            if ai_res:
                files_dict = extract_json_from_llm(ai_res)
                if isinstance(files_dict, dict) and ("server.py" in files_dict or "index.html" in files_dict):
                    # Ensure critical runnable files exist if omitted by LLM
                    fallback_files = cls.generate_project_source_files(project_name, blueprint)
                    for required_key in ["requirements.txt", "test_suite.py", ".gitignore", "vercel.json", "styles.css", "app.js", "server.py"]:
                        if required_key not in files_dict and required_key in fallback_files:
                            files_dict[required_key] = fallback_files[required_key]

                    logger.info(f"AI successfully generated {len(files_dict)} tailored source files.")
                    return files_dict
                else:
                    logger.warning(f"AI response did not yield valid file dictionary: {str(ai_res)[:200]}")
        except Exception as e:
            logger.error(f"AI source code synthesis failed: {e}", exc_info=True)

        logger.info("Falling back to deterministic dynamic blueprint code generation.")
        return cls.generate_project_source_files(project_name, blueprint)

    async def build_and_persist_workspace(
        self,
        db: AsyncSession,
        project_id: str,
        project_name: str,
        blueprint: Dict[str, Any],
        tech_stack: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Write generated source files to workspace and persist in database.
        Uses AI-powered synthesis when use_ai is True and AI is configured.
        """
        workspace_dir = self.get_workspace_dir(project_id, project_name)
        if use_ai and settings.ai_configured:
            files = await self.generate_project_source_files_with_ai(
                project_name=project_name,
                blueprint=blueprint,
                tech_stack=tech_stack,
                custom_instructions=custom_instructions,
            )
        else:
            files = self.generate_project_source_files(project_name, blueprint)

        # Validate against path traversal and syntax errors
        persisted_files = []
        for file_path, content in files.items():
            # Security: Path traversal protection
            rel_path = Path(file_path)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                raise ValueError(f"Security Alert: Path traversal attempt detected in filename '{file_path}'")

            full_path = (workspace_dir / file_path).resolve()
            if not str(full_path).startswith(str(workspace_dir.resolve())):
                raise ValueError(f"Security Alert: Resolved path '{full_path}' is outside workspace '{workspace_dir}'")

            # Syntax validation: parse python files before persisting
            if file_path.endswith(".py"):
                import ast
                try:
                    ast.parse(content, filename=file_path)
                except SyntaxError as e:
                    logger.error(f"Generated python file '{file_path}' has syntax error: {e}")
                    raise ValueError(f"Generated Python file '{file_path}' contains syntax error: {e}")

            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

            # Check if file record already exists in DB
            res = await db.execute(
                select(ProjectFile).where(
                    ProjectFile.project_id == project_id,
                    ProjectFile.path == file_path,
                )
            )
            existing_file = res.scalar_one_or_none()
            if existing_file:
                existing_file.content = content
                existing_file.version += 1
                persisted_files.append(existing_file)
            else:
                ext = file_path.split(".")[-1]
                lang_map = {"py": "python", "js": "javascript", "html": "html", "css": "css", "md": "markdown", "json": "json"}
                pf = ProjectFile(
                    project_id=project_id,
                    path=file_path,
                    content=content,
                    language=lang_map.get(ext, "text"),
                    version=1,
                )
                db.add(pf)
                persisted_files.append(pf)

        # Repair server syntax if needed
        server_path = workspace_dir / "server.py"
        if server_path.exists():
            self.repair_server_syntax(server_path)

        await db.commit()
        return {
            "workspace_dir": str(workspace_dir),
            "files_written": list(files.keys()),
            "total_files": len(files),
            "ai_generated": bool(use_ai and settings.ai_configured),
        }

    @staticmethod
    def repair_server_syntax(server_file: Path) -> bool:
        """
        Self-repair syntax errors or unterminated string literals in server.py
        before verification tests run.
        """
        if not server_file.exists():
            return False
        try:
            import ast
            import re
            code = server_file.read_text(encoding="utf-8")
            try:
                ast.parse(code)
                return True
            except SyntaxError:
                pass

            # Primary repair: Fix unescaped multiline description in FastAPI(...) initialization
            match = re.search(r'(app\s*=\s*FastAPI\([^)]*?description\s*=\s*)"([\s\S]*?)"(\s*,\s*version\s*=)', code)
            if match:
                prefix = match.group(1)
                raw_desc = match.group(2)
                suffix = match.group(3)
                cleaned_desc = " ".join(line.strip() for line in raw_desc.splitlines() if line.strip())
                safe_desc = json.dumps(cleaned_desc)
                repaired_code = code[:match.start()] + prefix + safe_desc + suffix + code[match.end():]
                try:
                    ast.parse(repaired_code)
                    server_file.write_text(repaired_code, encoding="utf-8")
                    logger.info(f"Self-healed FastAPI description syntax in {server_file}")
                    return True
                except SyntaxError:
                    pass

            # Secondary fallback repair
            # If docstrings or string literals have unclosed quotes
            fixed_code = code.replace('\r\n', '\n')
            # Check if replacing single-quotes or unterminated lines helps
            try:
                ast.parse(fixed_code)
                server_file.write_text(fixed_code, encoding="utf-8")
                return True
            except SyntaxError:
                pass
        except Exception as e:
            logger.warning(f"Server repair exception: {e}")
        return False

    @staticmethod
    async def run_workspace_tests(workspace_dir: Path) -> Dict[str, Any]:
        """
        Run automated pytest verification inside isolated workspace directory.
        """
        workspace_dir = Path(workspace_dir).resolve()
        if not workspace_dir.exists():
            return {"status": "error", "message": f"Workspace directory not found: {workspace_dir}", "passed": False}

        # Self-repair server.py syntax before executing tests if needed
        server_file = workspace_dir / "server.py"
        if server_file.exists():
            WorkspaceBuilder.repair_server_syntax(server_file)

        test_file = workspace_dir / "test_suite.py"
        if not test_file.exists():
            # Auto-generate test suite based on server.py
            server_file = workspace_dir / "server.py"
            server_code = server_file.read_text(encoding="utf-8") if server_file.exists() else ""

            health_path = "/api/v1/health" if "/api/v1/health" in server_code else "/api/health"
            has_discrepancies = "/api/v1/discrepancies" in server_code
            has_process = "/api/process" in server_code

            test_content = [
                'from fastapi.testclient import TestClient',
                'from server import app',
                '',
                'client = TestClient(app)',
                '',
                'def test_health():',
                f'    resp = client.get("{health_path}")',
                '    assert resp.status_code == 200',
                '    assert resp.json().get("status") == "healthy"',
                '',
            ]
            if has_discrepancies:
                test_content.extend([
                    'def test_metrics():',
                    '    resp = client.get("/api/v1/metrics/summary")',
                    '    assert resp.status_code == 200',
                    '    assert "total_events" in resp.json()',
                    '',
                    'def test_discrepancies():',
                    '    resp = client.get("/api/v1/discrepancies")',
                    '    assert resp.status_code == 200',
                    '    assert len(resp.json()) >= 1',
                    '',
                ])
            elif has_process:
                test_content.extend([
                    'def test_process():',
                    '    resp = client.post("/api/process", json={"payload": "automated test execution"})',
                    '    assert resp.status_code == 200',
                    '    assert resp.json().get("status") == "completed"',
                    '',
                ])
            test_file.write_text("\n".join(test_content), encoding="utf-8")

        # Execute pytest synchronously in a background worker thread to prevent Windows subprocess deadlocks
        def _exec_pytest(wdir: Path) -> Dict[str, Any]:
            try:
                res = subprocess.run(
                    [sys.executable, "-m", "pytest", "test_suite.py", "-v"],
                    cwd=str(wdir),
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                stdout_str = res.stdout or ""
                stderr_str = res.stderr or ""
                passed = (res.returncode == 0)
                return {
                    "status": "passed" if passed else "failed",
                    "passed": passed,
                    "returncode": res.returncode,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                }
            except subprocess.TimeoutExpired:
                return {"status": "timeout", "passed": False, "message": "Tests timed out after 20 seconds."}
            except Exception as e:
                return {"status": "error", "passed": False, "message": str(e)}

        return await asyncio.to_thread(_exec_pytest, workspace_dir)
