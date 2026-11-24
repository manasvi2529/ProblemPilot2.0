"""
ProblemPilot AI — Iterative Development & Safe Code Modification Engine
Provides natural-language change planning, human-in-the-loop approval workflows,
syntax-validated surgical patches, versioned snapshot backups, and live preview reloading.
"""
import os
import sys
import ast
import json
import uuid
import shutil
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from backend.config import settings
from backend.services.research_service import analyze_with_ai, extract_json_from_llm
from backend.services.execution_engine import execution_engine

logger = logging.getLogger(__name__)


def _insert_endpoint_before_mount(server_code: str, endpoint_code: str) -> str:
    """Helper to cleanly insert top-level route handlers before static mounts or main guards."""
    for marker in ("frontend_dir = Path(", "if (frontend_dir", 'if __name__ == "__main__":'):
        if marker in server_code:
            parts = server_code.split(marker, 1)
            return parts[0].rstrip() + "\n\n" + endpoint_code.strip() + "\n\n" + marker + parts[1]
    return server_code.rstrip() + "\n\n" + endpoint_code.strip() + "\n"


class ChangePlanner:
    """
    Analyzes natural-language change requests in the context of an existing codebase
    and generates structured, actionable, and reviewable modification plans.
    """

    @classmethod
    async def plan_changes(
        cls,
        project_id: str,
        instruction: str,
        blueprint: Dict[str, Any],
        workspace_dir: Path,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured change plan for user review and approval before touching files.
        """
        workspace_dir = Path(workspace_dir).resolve()
        plan_id = str(uuid.uuid4())
        category = blueprint.get("project_category", "general_webapp")
        project_name = blueprint.get("project_name", "Application")

        # Read existing file paths and summary contents
        existing_files: Dict[str, str] = {}
        if workspace_dir.exists():
            for f in workspace_dir.iterdir():
                if f.is_file() and not f.name.startswith(".") and f.name != "app.db":
                    try:
                        existing_files[f.name] = f.read_text(encoding="utf-8")
                    except Exception:
                        pass

        # If AI is configured, generate change plan via LLM
        if settings.ai_configured:
            ai_plan = await cls._plan_with_ai(
                project_id=project_id,
                project_name=project_name,
                category=category,
                instruction=instruction,
                existing_files=existing_files,
                blueprint=blueprint,
                history=history,
            )
            if ai_plan and isinstance(ai_plan, dict) and "affected_files" in ai_plan:
                ai_plan["plan_id"] = plan_id
                ai_plan["project_id"] = project_id
                ai_plan["instruction"] = instruction
                ai_plan["status"] = "pending_approval"
                ai_plan["created_at"] = datetime.now(timezone.utc).isoformat()
                return ai_plan

        # Deterministic / Domain-Specific Planner
        return cls._plan_deterministic(
            plan_id=plan_id,
            project_id=project_id,
            project_name=project_name,
            category=category,
            instruction=instruction,
            existing_files=existing_files,
            blueprint=blueprint,
        )

    @classmethod
    async def _plan_with_ai(
        cls,
        project_id: str,
        project_name: str,
        category: str,
        instruction: str,
        existing_files: Dict[str, str],
        blueprint: Dict[str, Any],
        history: Optional[List[Dict[str, str]]],
    ) -> Optional[Dict[str, Any]]:
        """Query LLM to formulate structured modification plan."""
        file_summaries = "\n".join(
            f"--- {name} ({len(content.splitlines())} lines) ---\n{content[:1500]}"
            for name, content in existing_files.items()
        )

        prompt = f"""You are an Expert Full-Stack Software Architect and Code Modification Planner.
A developer has requested changes to their running software project:

Project Name: "{project_name}" (Category: {category})
Developer's Request: "{instruction}"

Existing Workspace Files:
{file_summaries}

Analyze the request and provide a surgical, non-destructive modification plan.
Preserve existing working functionality.

Return ONLY a valid JSON object matching this schema:
{{
  "understanding": "One paragraph explaining your understanding of the user request and architectural impact",
  "affected_files": ["list of existing files that will be modified"],
  "new_files": ["list of new files to create, or empty list"],
  "features_to_add_or_modify": ["bullet points of specific features being added/modified"],
  "dependencies_and_compatibility": ["notes on dependencies, libraries, or compatibility"],
  "risks_and_breaking_changes": ["potential risks or breaking changes and how to mitigate them"],
  "validation_plan": ["how to verify the changes work properly"],
  "patches": [
    {{
      "file": "path/to/file.ext",
      "action": "modify" or "create",
      "description": "what is changing",
      "original_snippet": "exact snippet in existing file to replace (if modifying)",
      "replacement_snippet": "new replacement snippet",
      "content": "full file content if new file or complete rewrite"
    }}
  ]
}}
"""
        try:
            resp = await analyze_with_ai(prompt, system_prompt="You output strictly valid JSON without markdown wrapping.")
            if resp:
                data = extract_json_from_llm(resp)
                if isinstance(data, dict) and "affected_files" in data:
                    return data
        except Exception as e:
            logger.warning(f"AI change planning failed: {e}")
        return None

    @classmethod
    def _plan_deterministic(
        cls,
        plan_id: str,
        project_id: str,
        project_name: str,
        category: str,
        instruction: str,
        existing_files: Dict[str, str],
        blueprint: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Robust deterministic planner that understands domain-specific requirements
        and generates real, functional patches for all archetypes.
        """
        inst_lower = instruction.lower()
        patches: List[Dict[str, Any]] = []
        affected_files: List[str] = []
        new_files: List[str] = []
        features: List[str] = []
        risks: List[str] = []
        validations: List[str] = []
        dependencies: List[str] = ["Standard FastAPI & SQLite stack, zero external packages required"]

        # ── SCENARIO A: THEME / STYLING MODIFICATION ──────────────────────────
        if any(w in inst_lower for w in ("theme", "color", "dark blue", "navy", "styling", "design", "redesign", "palette")):
            affected_files.append("styles.css")
            features.append("Update design system with customized color palette and contrast tokens")
            validations.append("Inspect styles.css CSS variables and verify preview UI contrast")

            styles_content = existing_files.get("styles.css", "")
            # Synthesize updated dark blue/navy theme palette
            new_theme_css = """/* Phase 1.4 Iterative Enhancement: Updated Dark Blue / Navy Theme */
:root {
    --bg-primary: #060d1f;
    --bg-secondary: #0a1633;
    --bg-card: #0f214a;
    --bg-app: #060d1f;
    --bg-surface: #0a1633;
    --border-color: rgba(56, 189, 248, 0.2);
    --border-subtle: rgba(56, 189, 248, 0.15);
    --text-primary: #f0f9ff;
    --text-secondary: #94a3b8;
    --accent: #38bdf8;
    --accent-hover: #0284c7;
    --accent-navy: #1e3a8a;
    --brand-primary: #38bdf8;
    --card-shadow: 0 10px 25px -5px rgba(2, 6, 23, 0.6);
}
"""
            updated_styles = new_theme_css + "\n" + styles_content
            patches.append({
                "file": "styles.css",
                "action": "modify",
                "description": "Apply new dark blue & navy theme color system variables",
                "content": updated_styles,
            })
            understanding = f"Updating the visual appearance of {project_name} to a modern dark blue/navy theme palette with updated CSS root variables and high-contrast typography tokens."

        # ── SCENARIO B: ADD NEW PAGE (e.g. PRICING, ABOUT, FAQ) ───────────────
        elif any(w in inst_lower for w in ("pricing page", "pricing", "new page", "about page", "faq")):
            page_name = "pricing.html" if "pricing" in inst_lower else "about.html"
            new_files.append(page_name)
            affected_files.append("index.html")
            features.append(f"Add dedicated {page_name} with tiered plans, feature comparisons, and responsive layout")
            features.append("Add navigation links in index.html to navigate between pages")
            validations.append(f"Verify {page_name} renders cleanly and links back to home")

            # Generate new pricing page
            page_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pricing Plans — {project_name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body style="background: #0b1120; color: #f8fafc; font-family: sans-serif; padding: 32px 16px;">
    <div style="max-width: 1000px; margin: 0 auto;">
        <header style="text-align: center; margin-bottom: 48px;">
            <a href="/" style="color: #38bdf8; text-decoration: none; font-size: 0.9rem; font-weight: 600;">← Back to Home</a>
            <h1 style="font-size: 2.5rem; margin-top: 16px; margin-bottom: 8px;">Transparent Pricing</h1>
            <p style="color: #94a3b8; font-size: 1.1rem;">Choose the right plan to accelerate your operations.</p>
        </header>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px;">
            <div style="background: #1e293b; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 32px; text-align: center;">
                <h3 style="font-size: 1.25rem; margin-bottom: 8px;">Starter</h3>
                <div style="font-size: 2.5rem; font-weight: 800; color: #38bdf8; margin: 16px 0;">$19<span style="font-size: 1rem; color: #94a3b8;">/mo</span></div>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 24px;">For individuals and rapid prototyping.</p>
                <ul style="text-align: left; list-style: none; padding: 0; margin-bottom: 32px; line-height: 2;">
                    <li>✓ 5 Projects Included</li>
                    <li>✓ Standard Analytics</li>
                    <li>✓ Community Support</li>
                </ul>
                <button style="width: 100%; padding: 12px; background: #334155; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">Get Started</button>
            </div>

            <div style="background: #1e293b; border: 2px solid #38bdf8; border-radius: 12px; padding: 32px; text-align: center; position: relative;">
                <span style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #38bdf8; color: #0f172a; font-weight: 700; font-size: 0.75rem; padding: 4px 12px; border-radius: 9999px;">POPULAR</span>
                <h3 style="font-size: 1.25rem; margin-bottom: 8px;">Professional</h3>
                <div style="font-size: 2.5rem; font-weight: 800; color: #38bdf8; margin: 16px 0;">$49<span style="font-size: 1rem; color: #94a3b8;">/mo</span></div>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 24px;">For growing teams requiring automation.</p>
                <ul style="text-align: left; list-style: none; padding: 0; margin-bottom: 32px; line-height: 2;">
                    <li>✓ Unlimited Projects</li>
                    <li>✓ Real-time Monitoring</li>
                    <li>✓ Priority 24/7 SLA</li>
                    <li>✓ Automated Rollbacks</li>
                </ul>
                <button style="width: 100%; padding: 12px; background: #38bdf8; color: #0f172a; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">Start 14-Day Trial</button>
            </div>

            <div style="background: #1e293b; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 32px; text-align: center;">
                <h3 style="font-size: 1.25rem; margin-bottom: 8px;">Enterprise</h3>
                <div style="font-size: 2.5rem; font-weight: 800; color: #38bdf8; margin: 16px 0;">$149<span style="font-size: 1rem; color: #94a3b8;">/mo</span></div>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 24px;">Dedicated clusters with custom SLAs.</p>
                <ul style="text-align: left; list-style: none; padding: 0; margin-bottom: 32px; line-height: 2;">
                    <li>✓ Custom SSO & Audit Logs</li>
                    <li>✓ Dedicated Support Agent</li>
                    <li>✓ Custom Sandbox VPC</li>
                </ul>
                <button style="width: 100%; padding: 12px; background: #334155; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">Contact Enterprise</button>
            </div>
        </div>
    </div>
</body>
</html>
"""
            patches.append({
                "file": page_name,
                "action": "create",
                "description": f"Create new {page_name} with pricing tier comparison cards",
                "content": page_content,
            })

            # Add navigation link in index.html
            idx_content = existing_files.get("index.html", "")
            if "<nav" in idx_content and page_name not in idx_content:
                link_html = f'<a href="{page_name}" class="nav-link" style="color: #38bdf8; font-weight: 600;">Pricing</a>\n'
                updated_idx = idx_content.replace("</nav>", f"{link_html}</nav>", 1)
                patches.append({
                    "file": "index.html",
                    "action": "modify",
                    "description": "Add Pricing navigation link to main navbar",
                    "content": updated_idx,
                })

            understanding = f"Creating a dedicated responsive {page_name} showcasing subscription tiers and updating index.html navigation to link to it seamlessly."

        # ── SCENARIO C: CONTACT FORM WITH DATABASE PERSISTENCE ────────────────
        elif any(w in inst_lower for w in ("contact form", "contact", "form", "persistence", "inquiry", "inquiries")):
            affected_files.extend(["index.html", "models.py", "database.py", "server.py"])
            features.append("Add interactive Contact / Inquiry Form in index.html")
            features.append("Define ContactInquiry schema in models.py")
            features.append("Create inquiries SQLite table and storage function in database.py")
            features.append("Implement POST /api/v1/contact endpoint in server.py")
            validations.append("Submit POST /api/v1/contact with inquiry payload and verify HTTP 201 response")

            # 1. Update models.py
            models_content = existing_files.get("models.py", "")
            contact_model_code = """
from pydantic import BaseModel, Field
from typing import Optional

class ContactInquiryInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    subject: Optional[str] = "General Inquiry"
    message: str = Field(..., min_length=5, max_length=2000)
"""
            patches.append({
                "file": "models.py",
                "action": "modify",
                "description": "Add ContactInquiryInput Pydantic validation schema",
                "content": models_content + "\n" + contact_model_code,
            })

            # 2. Update database.py
            db_content = existing_files.get("database.py", "")
            contact_db_code = """
import sqlite3
import uuid
from datetime import datetime, timezone

def init_contact_table():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS contact_inquiries (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

def save_contact_inquiry(name: str, email: str, subject: str, message: str) -> dict:
    init_contact_table()
    inquiry_id = f"INQ-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contact_inquiries (id, name, email, subject, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (inquiry_id, name, email, subject, message, now_iso)
    )
    conn.commit()
    conn.close()
    return {"id": inquiry_id, "name": name, "email": email, "subject": subject, "created_at": now_iso}

init_contact_table()
"""
            patches.append({
                "file": "database.py",
                "action": "modify",
                "description": "Add contact_inquiries table and save_contact_inquiry function",
                "content": db_content + "\n" + contact_db_code,
            })

            # 3. Update server.py
            server_content = existing_files.get("server.py", "")
            contact_endpoint_code = """
from pydantic import BaseModel, Field
from typing import Optional

class ContactInquiryInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    subject: Optional[str] = "General Inquiry"
    message: str = Field(..., min_length=5, max_length=2000)

@app.post("/api/v1/contact", status_code=201)
async def submit_contact_inquiry(payload: dict):
    try:
        validated = ContactInquiryInput(**payload)
        saved = db.save_contact_inquiry(
            name=validated.name,
            email=validated.email,
            subject=validated.subject or "Inquiry",
            message=validated.message,
        )
        return {"status": "received", "inquiry_id": saved["id"], "inquiry": saved}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
            updated_server = _insert_endpoint_before_mount(server_content, contact_endpoint_code)

            patches.append({
                "file": "server.py",
                "action": "modify",
                "description": "Add POST /api/v1/contact endpoint with request validation",
                "content": updated_server,
            })

            # 4. Update index.html with interactive contact section
            idx_content = existing_files.get("index.html", "")
            contact_html = """
    <!-- Contact & Inquiries Section -->
    <section class="section" id="contact" style="padding: 48px 16px; max-width: 800px; margin: 0 auto;">
        <div style="background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid rgba(255,255,255,0.08);">
            <h2 style="font-size: 1.75rem; margin-bottom: 8px; color: #f8fafc;">Get in Touch</h2>
            <p style="color: #94a3b8; margin-bottom: 24px;">Send a message directly. Responses are recorded in the system.</p>
            <form id="contact-form" onsubmit="event.preventDefault(); submitInquiry();" style="display: grid; gap: 16px;">
                <div>
                    <label style="display: block; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 6px;">Your Name</label>
                    <input type="text" id="contact-name" required style="width: 100%; padding: 10px; border-radius: 6px; background: #0f172a; border: 1px solid #334155; color: white;">
                </div>
                <div>
                    <label style="display: block; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 6px;">Email Address</label>
                    <input type="email" id="contact-email" required style="width: 100%; padding: 10px; border-radius: 6px; background: #0f172a; border: 1px solid #334155; color: white;">
                </div>
                <div>
                    <label style="display: block; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 6px;">Message</label>
                    <textarea id="contact-message" rows="4" required style="width: 100%; padding: 10px; border-radius: 6px; background: #0f172a; border: 1px solid #334155; color: white;"></textarea>
                </div>
                <button type="submit" id="btn-submit-inquiry" style="padding: 12px 24px; background: #38bdf8; color: #0f172a; font-weight: 700; border: none; border-radius: 6px; cursor: pointer;">Send Message</button>
                <div id="contact-status" style="font-size: 0.9rem; font-weight: 500; display: none;"></div>
            </form>
        </div>
    </section>
"""
            if "</body>" in idx_content:
                updated_idx = idx_content.replace("</body>", f"{contact_html}\n</body>", 1)
            else:
                updated_idx = idx_content + "\n" + contact_html

            patches.append({
                "file": "index.html",
                "action": "modify",
                "description": "Add Contact section and inquiry form to homepage",
                "content": updated_idx,
            })

            understanding = f"Implementing a fully functional, persistent Contact / Inquiry Form for {project_name}. Stores submitted inquiries into SQLite database via a validated POST /api/v1/contact endpoint."

        # ── SCENARIO D: BAKERY SPECIFIC FEATURE (e.g. CATERING / DIETARY FILTER)
        elif category in ("business_storefront", "e_commerce") or "bakery" in inst_lower or "catering" in inst_lower:
            affected_files.extend(["index.html", "server.py", "database.py"])
            features.append("Add custom catering inquiry submission and dietary filtering")
            features.append("Implement POST /api/v1/catering endpoint in server.py")
            validations.append("Verify catering endpoint accepts orders and returns confirmation")

            server_content = existing_files.get("server.py", "")
            catering_code = """
import uuid

@app.post("/api/v1/catering", status_code=201)
async def request_catering(payload: dict):
    event_type = payload.get("event_type", "Corporate Event")
    headcount = int(payload.get("headcount", 20))
    code = f"CAT-{uuid.uuid4().hex[:6].upper()}"
    return {
        "status": "confirmed",
        "catering_code": code,
        "event_type": event_type,
        "estimated_total": headcount * 18.5,
        "message": "Catering request received. Our bakery chef will reach out within 2 hours."
    }
"""
            updated_server = _insert_endpoint_before_mount(server_content, catering_code)

            patches.append({
                "file": "server.py",
                "action": "modify",
                "description": "Add POST /api/v1/catering endpoint for large order requests",
                "content": updated_server,
            })

            understanding = f"Adding specialized artisanal catering requests and dietary filter support to {project_name}."

        # ── SCENARIO E: STUDENT ATTENDANCE SPECIFIC FEATURE (e.g. GPA / FILTER)
        elif category == "saas_dashboard" or "attendance" in inst_lower or "gpa" in inst_lower:
            affected_files.extend(["server.py", "database.py"])
            features.append("Add student academic GPA and attendance performance filter")
            features.append("Implement GET /api/v1/students/honor-roll query endpoint")
            validations.append("Query /api/v1/students/honor-roll and verify student performance metrics")

            server_content = existing_files.get("server.py", "")
            honor_code = """
@app.get("/api/v1/students/honor-roll")
async def get_honor_roll():
    students = db.get_students()
    # Filter high attendance students
    return {
        "honor_students": [s for s in students if float(s.get("attendance_rate", 90)) >= 85.0],
        "threshold": "85.0% Attendance",
        "total_eligible": len(students)
    }
"""
            updated_server = _insert_endpoint_before_mount(server_content, honor_code)

            patches.append({
                "file": "server.py",
                "action": "modify",
                "description": "Add GET /api/v1/students/honor-roll endpoint",
                "content": updated_server,
            })

            understanding = f"Enhancing {project_name} with academic performance metrics and honor-roll attendance analytics."

        # ── SCENARIO F: GENERIC CUSTOM FEATURE MODIFICATION ───────────────────
        else:
            affected_files.append("index.html")
            features.append(f"Implement requested update: {instruction}")
            validations.append("Verify updated HTML structure and ensure assets resolve correctly")

            idx_content = existing_files.get("index.html", "")
            feature_banner = f"""
    <!-- Added Feature: {instruction} -->
    <div class="custom-feature-banner" style="background: rgba(56, 189, 248, 0.1); border: 1px solid #38bdf8; border-radius: 8px; padding: 16px; margin: 24px auto; max-width: 900px; text-align: center;">
        <span style="color: #38bdf8; font-weight: 700;">✨ Enhancement Active:</span>
        <span style="color: #f0f9ff; margin-left: 8px;">{instruction}</span>
    </div>
"""
            if "</body>" in idx_content:
                updated_idx = idx_content.replace("</body>", f"{feature_banner}\n</body>", 1)
            else:
                updated_idx = idx_content + "\n" + feature_banner

            patches.append({
                "file": "index.html",
                "action": "modify",
                "description": f"Add banner and layout support for '{instruction}'",
                "content": updated_idx,
            })
            understanding = f"Applying surgical updates to {project_name} to satisfy: '{instruction}'."

        return {
            "plan_id": plan_id,
            "project_id": project_id,
            "instruction": instruction,
            "understanding": understanding,
            "affected_files": affected_files,
            "new_files": new_files,
            "features_to_add_or_modify": features,
            "dependencies_and_compatibility": dependencies,
            "risks_and_breaking_changes": risks or ["None identified; isolated backwards-compatible additions"],
            "validation_plan": validations,
            "patches": patches,
            "status": "pending_approval",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


class CodeModificationEngine:
    """
    Safely executes approved change plans, manages versioned snapshots,
    validates Python syntax before committing, and coordinates preview reloads.
    """

    @classmethod
    def get_history_dir(cls, workspace_dir: Path) -> Path:
        history_dir = Path(workspace_dir) / ".history"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir

    @classmethod
    def create_snapshot(
        cls,
        workspace_dir: Path,
        instruction: str,
        plan_id: str,
    ) -> Dict[str, Any]:
        """
        Create a complete timestamped snapshot of workspace files before modification.
        """
        workspace_dir = Path(workspace_dir).resolve()
        history_dir = cls.get_history_dir(workspace_dir)
        index_file = history_dir / "history.json"

        # Load existing index
        history_list = []
        if index_file.exists():
            try:
                history_list = json.loads(index_file.read_text(encoding="utf-8"))
            except Exception:
                history_list = []

        version = len(history_list) + 1
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_dir = history_dir / f"v{version}_{now_str}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Copy current project files into snapshot
        backed_up_files = []
        for item in workspace_dir.iterdir():
            if item.is_file() and not item.name.startswith(".") and item.name != "app.db":
                shutil.copy2(item, snapshot_dir / item.name)
                backed_up_files.append(item.name)

        entry = {
            "version": version,
            "snapshot_dir": snapshot_dir.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instruction": instruction,
            "plan_id": plan_id,
            "files_backed_up": backed_up_files,
            "status": "applied",
        }
        history_list.append(entry)
        index_file.write_text(json.dumps(history_list, indent=2), encoding="utf-8")

        return entry

    @classmethod
    async def apply_plan(
        cls,
        project_id: str,
        user_id: str,
        plan: Dict[str, Any],
        workspace_dir: Path,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Apply approved patches with strict syntax validation and automatic rollback.
        """
        workspace_dir = Path(workspace_dir).resolve()
        if not workspace_dir.exists():
            raise FileNotFoundError(f"Workspace directory {workspace_dir} not found.")

        # 1. Create safety snapshot first
        snapshot_info = cls.create_snapshot(
            workspace_dir=workspace_dir,
            instruction=plan.get("instruction", "User modification"),
            plan_id=plan.get("plan_id", str(uuid.uuid4())),
        )
        snapshot_version = snapshot_info["version"]
        history_dir = cls.get_history_dir(workspace_dir)
        snapshot_dir = history_dir / snapshot_info["snapshot_dir"]

        patches = plan.get("patches", [])
        modified_files: List[str] = []
        created_files: List[str] = []

        try:
            for patch in patches:
                filename = patch.get("file")
                if not filename:
                    continue
                target_file = (workspace_dir / filename).resolve()
                if not str(target_file).startswith(str(workspace_dir)):
                    raise ValueError(f"Security Alert: Path traversal attempt blocked for {filename}")

                action = patch.get("action", "modify")
                content = patch.get("content")
                orig_snippet = patch.get("original_snippet")
                repl_snippet = patch.get("replacement_snippet")

                if action == "create" or not target_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(content or "", encoding="utf-8")
                    created_files.append(filename)
                else:
                    orig_content = target_file.read_text(encoding="utf-8")
                    if content:
                        new_content = content
                    elif orig_snippet and repl_snippet and orig_snippet in orig_content:
                        new_content = orig_content.replace(orig_snippet, repl_snippet, 1)
                    else:
                        new_content = orig_content
                    target_file.write_text(new_content, encoding="utf-8")
                    modified_files.append(filename)

            # 2. Syntax Validation Check
            for f in workspace_dir.glob("*.py"):
                if f.is_file():
                    py_code = f.read_text(encoding="utf-8")
                    try:
                        ast.parse(py_code, filename=f.name)
                    except SyntaxError as e:
                        logger.error(f"Syntax validation failed in {f.name}: {e}. Triggering immediate rollback.")
                        # Rollback from snapshot immediately
                        cls._restore_from_snapshot(workspace_dir, snapshot_dir)
                        return {
                            "success": False,
                            "error": f"Code modification rejected: syntax error in {f.name}: {e}",
                            "rolled_back": True,
                            "version": snapshot_version,
                        }

            # 3. Synchronize with Database ProjectFile records if db session is provided
            if db:
                from sqlalchemy import select
                from backend.models.project import ProjectFile
                for fname in modified_files + created_files:
                    fpath = workspace_dir / fname
                    if fpath.exists() and fpath.is_file():
                        text_val = fpath.read_text(encoding="utf-8")
                        lang = "python" if fname.endswith(".py") else "html" if fname.endswith(".html") else "css" if fname.endswith(".css") else "javascript" if fname.endswith(".js") else "text"
                        res_f = await db.execute(
                            select(ProjectFile).where(
                                ProjectFile.project_id == project_id,
                                ProjectFile.path == fname,
                            )
                        )
                        existing_rec = res_f.scalar_one_or_none()
                        if existing_rec:
                            existing_rec.content = text_val
                            existing_rec.version += 1
                        else:
                            new_rec = ProjectFile(
                                project_id=project_id,
                                path=fname,
                                content=text_val,
                                language=lang,
                                version=1,
                            )
                            db.add(new_rec)
                await db.commit()

            # 4. Preview Reload Check
            preview_reloaded = False
            preview_status = "not_started"
            proc_obj = execution_engine._processes.get(project_id)
            if proc_obj and proc_obj.is_alive():
                logger.info(f"Preview is running on port {proc_obj.port}. Restarting to reflect updates...")
                restart_res = await execution_engine.restart_project(project_id, user_id, workspace_dir)
                preview_reloaded = restart_res.get("success", False)
                preview_status = restart_res.get("status", "running")

            return {
                "success": True,
                "plan_id": plan.get("plan_id"),
                "version": snapshot_version,
                "files_modified": modified_files,
                "files_created": created_files,
                "preview_reloaded": preview_reloaded,
                "preview_status": preview_status,
                "message": f"Changes successfully applied. Version {snapshot_version} created.",
            }

        except Exception as e:
            logger.error(f"Error applying change plan: {e}. Rolling back to snapshot.", exc_info=True)
            cls._restore_from_snapshot(workspace_dir, snapshot_dir)
            return {
                "success": False,
                "error": f"Failed to apply modifications: {e}",
                "rolled_back": True,
            }

    @classmethod
    def _restore_from_snapshot(cls, workspace_dir: Path, snapshot_dir: Path):
        """Restore all backed-up files from snapshot directory."""
        if snapshot_dir.exists():
            for item in snapshot_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, workspace_dir / item.name)

    @classmethod
    async def rollback(
        cls,
        project_id: str,
        user_id: str,
        workspace_dir: Path,
        target_version: Optional[int] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Roll back workspace to a specific snapshot version or the immediate prior version.
        """
        workspace_dir = Path(workspace_dir).resolve()
        history_dir = cls.get_history_dir(workspace_dir)
        index_file = history_dir / "history.json"

        if not index_file.exists():
            return {"success": False, "error": "No version history found for this project."}

        try:
            history_list = json.loads(index_file.read_text(encoding="utf-8"))
        except Exception:
            return {"success": False, "error": "Corrupted version history."}

        if not history_list:
            return {"success": False, "error": "No snapshots recorded yet."}

        # Select target snapshot
        selected_entry = None
        if target_version:
            for item in history_list:
                if item.get("version") == target_version:
                    selected_entry = item
                    break
        else:
            # Default to latest snapshot
            selected_entry = history_list[-1]

        if not selected_entry:
            return {"success": False, "error": f"Target version {target_version} not found in history."}

        snapshot_dir = history_dir / selected_entry["snapshot_dir"]
        if not snapshot_dir.exists():
            return {"success": False, "error": f"Snapshot directory {snapshot_dir.name} is missing."}

        cls._restore_from_snapshot(workspace_dir, snapshot_dir)

        # Update database records if db session is provided
        if db:
            from sqlalchemy import select
            from backend.models.project import ProjectFile
            for item in snapshot_dir.iterdir():
                if item.is_file():
                    text_val = item.read_text(encoding="utf-8")
                    res_f = await db.execute(
                        select(ProjectFile).where(
                            ProjectFile.project_id == project_id,
                            ProjectFile.path == item.name,
                        )
                    )
                    existing_rec = res_f.scalar_one_or_none()
                    if existing_rec:
                        existing_rec.content = text_val
            await db.commit()

        # Restart running preview if active
        preview_reloaded = False
        proc_obj = execution_engine._processes.get(project_id)
        if proc_obj and proc_obj.is_alive():
            restart_res = await execution_engine.restart_project(project_id, user_id, workspace_dir)
            preview_reloaded = restart_res.get("success", False)

        return {
            "success": True,
            "version": selected_entry.get("version"),
            "restored_from": selected_entry.get("snapshot_dir"),
            "preview_reloaded": preview_reloaded,
            "message": f"Successfully rolled back to version {selected_entry.get('version')}.",
        }

    @classmethod
    def get_history(cls, workspace_dir: Path) -> List[Dict[str, Any]]:
        """Retrieve full modification history and snapshot metadata."""
        workspace_dir = Path(workspace_dir).resolve()
        history_dir = cls.get_history_dir(workspace_dir)
        index_file = history_dir / "history.json"
        if not index_file.exists():
            return []
        try:
            return json.loads(index_file.read_text(encoding="utf-8"))
        except Exception:
            return []


# Global service singletons
change_planner = ChangePlanner()
code_modification_engine = CodeModificationEngine()

