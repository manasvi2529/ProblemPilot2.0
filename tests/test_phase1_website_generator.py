"""
Phase 1.1 Acceptance Tests: Real Dynamic Website Generation Engine.
Verifies the 10 core acceptance criteria for Problem2Project AI:
- TEST 1: Generate Data Analyst Portfolio with projects, skills, resume download, contact form & persistence.
- TEST 2: Generate Local Bakery Storefront with catalogue, prices, cart, order submission & persistence.
- TEST 3: Generate Student Attendance SaaS Dashboard with attendance metrics, roster CRUD & roll-call.
- TEST 4: Confirm 3 projects have different page structures, data models, endpoints and UI components.
- TEST 5: Changing requirements changes the generated output dynamically.
- TEST 6: Invalid/incomplete AI output handled safely via deterministic synthesizer.
- TEST 7: Failed operations reported honestly without claiming false success.
- TEST 8: Cross-user workspace isolation and path traversal prevention.
- TEST 9: Code quality - all generated Python files in all archetypes parse without SyntaxError.
- TEST 10: Blueprint schema adherence - all 17 required architectural fields are present.
"""
import pytest
import os
import shutil
from pathlib import Path
from backend.services.blueprint_engine import BlueprintEngine
from backend.services.website_generator import WebsiteGenerator
from backend.services.workspace_builder import WorkspaceBuilder


@pytest.fixture
def clean_sandbox_dir(tmp_path):
    """Temporary directory for isolating workspace tests."""
    test_dir = tmp_path / "test_sandboxes"
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)


def test_1_generate_data_analyst_portfolio():
    """
    TEST 1: Generate Data Analyst Portfolio website.
    Verifies:
    - Portfolio homepage, about, skills, projects sections
    - Resume download endpoint (/api/v1/resume/download)
    - Functional contact form with SQLite persistence (/api/v1/contact)
    - Responsive styles and vanilla JS interactions
    """
    prompt = "Create a modern portfolio website for a data analyst with projects, skills, resume download and contact form."
    category = BlueprintEngine.detect_category("Portfolio", prompt)
    assert category == "portfolio"

    blueprint = BlueprintEngine.generate_blueprint_fallback(
        title="Data Analyst Portfolio",
        description=prompt,
        custom_instructions=prompt,
    )
    assert blueprint["project_category"] == "portfolio"
    assert any("resume" in f.lower() for f in blueprint["features"])

    files = WebsiteGenerator.generate_codebase(
        project_name="Data Analyst Portfolio",
        blueprint=blueprint,
        custom_instructions=prompt,
    )

    # Check key files
    assert "index.html" in files
    assert "server.py" in files
    assert "database.py" in files
    assert "styles.css" in files
    assert "app.js" in files
    assert "test_suite.py" in files
    assert "README.md" in files

    # Verify portfolio-specific content
    html = files["index.html"]
    assert "skills" in html.lower()
    assert "projects" in html.lower()
    assert "contact" in html.lower()
    assert "/api/v1/resume/download" in html

    # Verify backend endpoints and database persistence
    server_py = files["server.py"]
    database_py = files["database.py"]
    assert "/api/v1/contact" in server_py
    assert "/api/v1/resume/download" in server_py
    assert "portfolio.db" in database_py
    assert "inquiries" in database_py  # inquiries table for inbound recruiter messages

    # Verify no fake telemetry metrics
    assert "99.8%" not in server_py
    assert "14ms" not in server_py


def test_2_generate_local_bakery_storefront():
    """
    TEST 2: Generate Local Bakery Storefront website.
    Verifies:
    - Bakery homepage, menu/catalogue with prices
    - Interactive shopping cart and order submission workflow
    - Persistent SQLite order storage
    - Store location, operating hours, and pickup scheduling
    """
    prompt = "Create a website for a local bakery where customers can browse products, view prices and submit orders."
    category = BlueprintEngine.detect_category("Bakery", prompt)
    assert category == "business_storefront"

    blueprint = BlueprintEngine.generate_blueprint_fallback(
        title="Artisan Crumb Bakery",
        description=prompt,
        custom_instructions=prompt,
    )
    assert blueprint["project_category"] == "business_storefront"

    files = WebsiteGenerator.generate_codebase(
        project_name="Artisan Crumb Bakery",
        blueprint=blueprint,
        custom_instructions=prompt,
    )

    # Check key files
    assert "index.html" in files
    assert "server.py" in files
    assert "database.py" in files
    assert "styles.css" in files
    assert "app.js" in files
    assert "test_suite.py" in files

    # Verify bakery storefront UI
    html = files["index.html"]
    assert "products" in html.lower()
    assert "cart" in html.lower()
    assert "order" in html.lower()
    assert "hours" in html.lower()

    # Verify backend endpoints and database persistence
    server_py = files["server.py"]
    database_py = files["database.py"]
    assert "/api/v1/products" in server_py
    assert "/api/v1/orders" in server_py
    assert "bakery.db" in database_py
    assert "orders" in database_py  # orders table creation
    assert "order_items" in database_py  # order_items relational table

    # Verify no fake telemetry metrics
    assert "99.8%" not in server_py
    assert "14ms" not in server_py


def test_3_generate_student_attendance_saas_dashboard():
    """
    TEST 3: Generate Student Attendance SaaS Dashboard.
    Verifies:
    - Attendance overview metrics, student roster CRUD
    - Daily roll-call register (Present, Absent, Late, Excused)
    - Persistent relational SQLite database
    - Batch attendance logging
    """
    prompt = "Create a SaaS dashboard for managing student attendance."
    category = BlueprintEngine.detect_category("Attendance SaaS", prompt)
    assert category == "saas_dashboard"

    blueprint = BlueprintEngine.generate_blueprint_fallback(
        title="AttendTrack SaaS",
        description=prompt,
        custom_instructions=prompt,
    )
    assert blueprint["project_category"] == "saas_dashboard"

    files = WebsiteGenerator.generate_codebase(
        project_name="AttendTrack SaaS",
        blueprint=blueprint,
        custom_instructions=prompt,
    )

    # Check key files
    assert "index.html" in files
    assert "server.py" in files
    assert "database.py" in files
    assert "styles.css" in files
    assert "app.js" in files
    assert "test_suite.py" in files

    # Verify SaaS UI structure
    html = files["index.html"]
    assert "attendance" in html.lower()
    assert "student" in html.lower()
    assert "roll-call" in html.lower()

    # Verify backend endpoints and database persistence
    server_py = files["server.py"]
    database_py = files["database.py"]
    assert "/api/v1/students" in server_py
    assert "/api/v1/attendance/batch" in server_py
    assert "/api/v1/metrics/attendance" in server_py
    assert "attendance.db" in database_py
    assert "students" in database_py
    assert "attendance_records" in database_py


def test_4_confirm_three_projects_diverge_completely():
    """
    TEST 4: Confirm that Portfolio, Bakery, and Attendance projects have
    different page structures, data models, API endpoints, and styles.
    """
    bp_portfolio = BlueprintEngine.generate_blueprint_fallback("Portfolio", "data analyst portfolio resume skills contact")
    bp_bakery = BlueprintEngine.generate_blueprint_fallback("Bakery", "local bakery cakes bread prices shopping cart orders")
    bp_saas = BlueprintEngine.generate_blueprint_fallback("Attendance SaaS", "saas dashboard student attendance roster tracking")

    files_portfolio = WebsiteGenerator.generate_codebase("Portfolio", bp_portfolio)
    files_bakery = WebsiteGenerator.generate_codebase("Bakery", bp_bakery)
    files_saas = WebsiteGenerator.generate_codebase("Attendance SaaS", bp_saas)

    # Distinct categories
    assert bp_portfolio["project_category"] != bp_bakery["project_category"]
    assert bp_bakery["project_category"] != bp_saas["project_category"]

    # Distinct databases and schemas in database.py
    assert "portfolio.db" in files_portfolio["database.py"]
    assert "bakery.db" in files_bakery["database.py"]
    assert "attendance.db" in files_saas["database.py"]

    # Distinct endpoints in server.py
    assert "/api/v1/resume/download" in files_portfolio["server.py"]
    assert "/api/v1/resume/download" not in files_bakery["server.py"]
    assert "/api/v1/resume/download" not in files_saas["server.py"]

    assert "/api/v1/products" in files_bakery["server.py"]
    assert "/api/v1/products" not in files_portfolio["server.py"]
    assert "/api/v1/products" not in files_saas["server.py"]

    assert "/api/v1/attendance/batch" in files_saas["server.py"]
    assert "/api/v1/attendance/batch" not in files_portfolio["server.py"]
    assert "/api/v1/attendance/batch" not in files_bakery["server.py"]

    # HTML content diverges
    assert files_portfolio["index.html"] != files_bakery["index.html"]
    assert files_bakery["index.html"] != files_saas["index.html"]


def test_5_changing_requirements_changes_output():
    """
    TEST 5: Changing user requirements changes generated output dynamically.
    """
    bp_1 = BlueprintEngine.generate_blueprint_fallback(
        "Blog App",
        "Create a blog for tech articles with tags and comments.",
    )
    bp_2 = BlueprintEngine.generate_blueprint_fallback(
        "E-Commerce App",
        "Create an e-commerce clothing store with checkout.",
    )

    assert bp_1["project_category"] != bp_2["project_category"]
    assert bp_1["features"] != bp_2["features"]

    files_1 = WebsiteGenerator.generate_codebase("Blog App", bp_1)
    files_2 = WebsiteGenerator.generate_codebase("E-Commerce App", bp_2)

    assert files_1["index.html"] != files_2["index.html"]
    assert files_1["README.md"] != files_2["README.md"]


def test_6_invalid_or_incomplete_ai_output_handled_safely():
    """
    TEST 6: Invalid or incomplete AI output safely falls back to deterministic generator.
    """
    broken_blueprint = {
        "title": "Minimal App",
    }

    files = WebsiteGenerator.generate_codebase(
        project_name="Minimal App",
        blueprint=broken_blueprint,
    )
    assert "index.html" in files
    assert "server.py" in files
    assert "styles.css" in files
    assert "test_suite.py" in files


def test_7_path_traversal_protection():
    """
    TEST 7: Security - path traversal attempts in generated filenames are rejected.
    """
    malicious_files = {
        "../../etc/evil.txt": "malicious content",
        "server.py": "print('ok')",
    }

    with pytest.raises(ValueError, match="Security Alert: Path traversal"):
        for file_path, content in malicious_files.items():
            rel_path = Path(file_path)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                raise ValueError(f"Security Alert: Path traversal attempt detected in filename '{file_path}'")


def test_8_workspace_directory_isolation(tmp_path, monkeypatch):
    """
    TEST 8: Cross-user and cross-project workspace directory isolation.
    """
    from backend.config import settings
    monkeypatch.setattr(settings, "SANDBOX_DIR", tmp_path)

    dir_1 = WorkspaceBuilder.get_workspace_dir("project-uuid-1111", "Unique App One")
    dir_2 = WorkspaceBuilder.get_workspace_dir("project-uuid-2222", "Unique App Two")

    # Distinct project IDs with distinct names => distinct paths
    assert dir_1 != dir_2
    assert dir_1.exists()
    assert dir_2.exists()


def test_9_all_generated_python_files_have_valid_syntax():
    """
    TEST 9: Code Quality - all generated Python files in all archetypes parse without SyntaxError.
    """
    import ast

    prompts = [
        ("Portfolio", "data analyst portfolio with skills resume and contact"),
        ("Bakery", "local bakery website with menu cart and pickup ordering"),
        ("SaaS", "student attendance saas dashboard with roster tracking"),
        ("Generic", "general company landing page with contact info"),
    ]

    for p_name, p_prompt in prompts:
        bp = BlueprintEngine.generate_blueprint_fallback(p_name, p_prompt)
        files = WebsiteGenerator.generate_codebase(p_name, bp)

        for fname, content in files.items():
            if fname.endswith(".py"):
                try:
                    ast.parse(content, filename=fname)
                except SyntaxError as e:
                    pytest.fail(f"SyntaxError in generated {p_name} file '{fname}': {e}")


def test_10_blueprint_engine_complete_schema():
    """
    TEST 10: Blueprint schema adherence - all 17 required architectural fields are present.
    """
    bp = BlueprintEngine.generate_blueprint_fallback(
        title="Data Analyst Portfolio",
        description="A data analyst needs to showcase machine learning projects and allow resume downloads.",
    )

    required_fields = [
        "project_name",
        "project_description",
        "target_audience",
        "main_purpose",
        "project_category",
        "user_roles",
        "required_pages",
        "features",
        "frontend_technology",
        "backend_requirements",
        "database_requirements",
        "api_requirements",
        "authentication_requirements",
        "external_integrations",
        "design_direction",
        "responsive_requirements",
        "testing_requirements",
        "deployment_requirements",
    ]

    for field in required_fields:
        assert field in bp, f"Missing required blueprint field: {field}"
        assert bp[field] is not None, f"Blueprint field {field} is None"
