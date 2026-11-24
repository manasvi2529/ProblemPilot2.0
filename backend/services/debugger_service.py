"""
Problem2Project AI — AI-Assisted Debugger & Targeted Repair Service.

Responsibilities:
1. Parse runtime error logs and exception tracebacks.
2. Pinpoint failing source file, line number, and error root-cause.
3. Formulate clear, human-intelligible explanation of what broke.
4. Generate precise targeted fixes (original code snippet -> replacement).
5. Apply fixes with automatic versioned backup to guarantee safe rollback.
6. Support one-click rollback if fix is rejected or does not resolve the error.
"""
import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from backend.config import settings
from backend.services.research_service import analyze_with_ai

logger = logging.getLogger(__name__)


class DebuggerService:
    """Intelligent diagnostics and bounded targeted code repair engine."""

    @staticmethod
    def parse_error_trace(logs: List[str]) -> Dict[str, Any]:
        """
        Extract relevant file path, line number, exception type, and description
        from standard Python tracebacks.
        """
        combined = "\n".join(logs)

        # 1. Regex for Python traceback File "path", line X, in Y
        matches = list(re.finditer(r'File\s+"([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+([^\n]+))?', combined))
        failing_file = None
        line_num = None
        function_name = None

        if matches:
            last_match = matches[-1]
            failing_file = Path(last_match.group(1)).name
            line_num = int(last_match.group(2))
            function_name = last_match.group(3)

        # 2. Extract exception line (e.g. TypeError: ... or SyntaxError: ... or ModuleNotFoundError: ...)
        exc_match = re.search(r'([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception):\s*([^\n]+)', combined)
        exc_type = exc_match.group(1) if exc_match else "RuntimeError"
        exc_detail = exc_match.group(2) if exc_match else "Application process failed unexpectedly"

        return {
            "file": failing_file,
            "line": line_num,
            "function": function_name,
            "exception_type": exc_type,
            "exception_detail": exc_detail.strip(),
            "has_trace": bool(matches),
        }

    async def diagnose_error(
        self,
        project_id: str,
        workspace_dir: Path,
        logs: List[str],
        custom_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze logs, locate failing code, explain the error simply,
        and generate a targeted code patch.
        """
        workspace_dir = Path(workspace_dir).resolve()
        trace_info = self.parse_error_trace(logs)
        failing_file = trace_info.get("file") or "server.py"
        line_num = trace_info.get("line")

        # Read context from target file if it exists
        target_path = workspace_dir / failing_file
        code_context = ""
        full_code = ""
        if target_path.exists() and target_path.is_file():
            try:
                full_code = target_path.read_text(encoding="utf-8")
                lines = full_code.splitlines()
                if line_num and 1 <= line_num <= len(lines):
                    start = max(0, line_num - 15)
                    end = min(len(lines), line_num + 15)
                    snippet_lines = []
                    for idx in range(start, end):
                        prefix = ">>> " if idx + 1 == line_num else "    "
                        snippet_lines.append(f"{prefix}{idx+1}: {lines[idx]}")
                    code_context = "\n".join(snippet_lines)
                else:
                    code_context = "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines[:50]))
            except Exception as e:
                logger.warning(f"Failed to read context from {target_path}: {e}")

        exc_type = trace_info["exception_type"]
        exc_detail = trace_info["exception_detail"]
        combined_logs = "\n".join(logs[-30:])

        # If AI is configured, query LLM for diagnosis and targeted patch
        if settings.ai_configured:
            prompt = f"""You are an Expert Software Debugger. Analyze this failure in project {project_id}:

Failing File: {failing_file} (around line {line_num or 'unknown'})
Exception: {exc_type}: {exc_detail}

Recent Logs:
{combined_logs}

Relevant Code Context:
```python
{code_context or full_code[:2000]}
```

Provide a structured JSON output with:
1. "summary": One-sentence plain-English explanation of the error.
2. "root_cause": Detailed technical explanation in simple language.
3. "file": The file path relative to workspace to modify (e.g. "{failing_file}").
4. "original_snippet": The exact lines of code that need to be replaced.
5. "replacement_snippet": The exact replacement code that fixes the issue.
6. "explanation_of_fix": Why this fix resolves the problem without breaking other features.

Return ONLY valid JSON matching this schema.
"""
            try:
                ai_resp = await analyze_with_ai(prompt, system_prompt="You output strictly valid JSON without markdown wrapping.")
                from backend.services.research_service import extract_json_from_llm
                diagnosis = extract_json_from_llm(ai_resp)
                if isinstance(diagnosis, dict) and "summary" in diagnosis:
                    diagnosis["project_id"] = project_id
                    diagnosis["trace_info"] = trace_info
                    return diagnosis
            except Exception as e:
                logger.warning(f"AI diagnosis failed: {e}")

        # Deterministic / heuristic fallback diagnosis
        summary = f"{exc_type}: {exc_detail}"
        root_cause = f"The application encountered an unhandled {exc_type} in {failing_file} (line {line_num or 'N/A'})."
        original_snippet = ""
        replacement_snippet = ""

        # Check for common patterns:
        if "Address already in use" in exc_detail or "Errno 98" in exc_detail or "Errno 10048" in exc_detail:
            summary = "Port Conflict Detected"
            root_cause = "Another process or previous instance is already bound to this TCP port."
            original_snippet = "port = 8030"
            replacement_snippet = "import os\nport = int(os.environ.get('PORT', 8030))"
        elif "ModuleNotFoundError" in exc_type or "ImportError" in exc_type:
            summary = f"Missing Dependency or Module in {failing_file}"
            root_cause = f"The python runtime could not resolve: {exc_detail}."
        elif "SyntaxError" in exc_type:
            summary = f"Python Syntax Error in {failing_file}"
            root_cause = f"Invalid Python syntax near line {line_num}: {exc_detail}."

        return {
            "project_id": project_id,
            "summary": summary,
            "root_cause": root_cause,
            "file": failing_file,
            "original_snippet": original_snippet,
            "replacement_snippet": replacement_snippet,
            "explanation_of_fix": "Targeted patch to correct the failing line or configuration.",
            "trace_info": trace_info,
        }

    @staticmethod
    def apply_fix(
        workspace_dir: Path,
        file_path: str,
        original_snippet: str,
        replacement_snippet: str,
    ) -> Dict[str, Any]:
        """
        Apply a targeted code patch to workspace file with automatic backup.
        """
        workspace_dir = Path(workspace_dir).resolve()
        target_file = (workspace_dir / file_path).resolve()

        if not str(target_file).startswith(str(workspace_dir)):
            raise ValueError(f"Security Alert: Resolved path {target_file} is outside workspace {workspace_dir}")

        if not target_file.exists() or not target_file.is_file():
            raise FileNotFoundError(f"Target file {file_path} not found in workspace.")

        original_content = target_file.read_text(encoding="utf-8")

        # Create timestamped backup file
        backup_file = target_file.with_suffix(f"{target_file.suffix}.bak")
        backup_file.write_text(original_content, encoding="utf-8")

        # Apply replacement
        if original_snippet and original_snippet in original_content:
            new_content = original_content.replace(original_snippet, replacement_snippet, 1)
        elif not original_snippet and replacement_snippet:
            # Full replacement or append
            new_content = replacement_snippet
        else:
            return {
                "success": False,
                "message": f"Original snippet not found in {file_path}. No changes applied.",
                "backup_created": False,
            }

        # Check Python syntax if python file
        if file_path.endswith(".py"):
            import ast
            try:
                ast.parse(new_content, filename=file_path)
            except SyntaxError as e:
                # Revert immediately
                target_file.write_text(original_content, encoding="utf-8")
                return {
                    "success": False,
                    "message": f"Fix rejected: replacement introduces syntax error: {e}",
                    "backup_created": False,
                }

        target_file.write_text(new_content, encoding="utf-8")
        logger.info(f"Successfully applied targeted fix to {target_file}. Backup saved to {backup_file.name}")

        return {
            "success": True,
            "file": file_path,
            "backup_file": backup_file.name,
            "message": f"Fix successfully applied to {file_path}. Backup created.",
        }

    @staticmethod
    def rollback_fix(workspace_dir: Path, file_path: str) -> Dict[str, Any]:
        """
        Restore file from its backup version (.bak).
        """
        workspace_dir = Path(workspace_dir).resolve()
        target_file = (workspace_dir / file_path).resolve()
        backup_file = target_file.with_suffix(f"{target_file.suffix}.bak")

        if not backup_file.exists():
            return {
                "success": False,
                "message": f"No backup file ({backup_file.name}) found to rollback.",
            }

        backup_content = backup_file.read_text(encoding="utf-8")
        target_file.write_text(backup_content, encoding="utf-8")
        backup_file.unlink(missing_ok=True)

        logger.info(f"Successfully rolled back {target_file} from backup.")
        return {
            "success": True,
            "file": file_path,
            "message": f"Successfully rolled back {file_path} to previous version.",
        }


# Global singleton instance
debugger_service = DebuggerService()

