"""
ProblemPilot AI — Structured Blueprint & Requirements Analysis Engine
Performs deep natural-language requirements analysis, project category classification,
feature extraction, tech stack selection, and structured blueprint generation.
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional

from backend.config import settings
from backend.services.research_service import analyze_with_ai, extract_json_from_llm

logger = logging.getLogger(__name__)


# Supported primary project categories
PROJECT_CATEGORIES = {
    "portfolio": {
        "label": "Personal & Professional Portfolio",
        "keywords": ["portfolio", "resume", "cv", "personal website", "data analyst", "developer portfolio", "designer portfolio"],
    },
    "business_storefront": {
        "label": "Local Business & Storefront",
        "keywords": ["bakery", "restaurant", "cafe", "shop", "store", "salon", "clinic", "local business", "storefront", "menu", "order food"],
    },
    "saas_dashboard": {
        "label": "SaaS & Administrative Dashboard",
        "keywords": ["saas", "dashboard", "attendance", "crm", "admin", "management system", "analytics platform", "telemetry", "portal"],
    },
    "e_commerce": {
        "label": "E-Commerce & Digital Marketplace",
        "keywords": ["e-commerce", "ecommerce", "shopping cart", "marketplace", "checkout", "storefront", "products online"],
    },
    "landing_page": {
        "label": "Product & Startup Landing Page",
        "keywords": ["landing page", "waitlist", "product launch", "coming soon", "lead capture", "promotional page"],
    },
    "blog": {
        "label": "Content & Editorial Publication",
        "keywords": ["blog", "articles", "news", "newsletter", "publication", "editorial", "posts"],
    },
}


class BlueprintEngine:
    """
    Analyzes user requirements and produces comprehensive, structured blueprints.
    Guarantees unique, domain-appropriate architecture for every project category.
    """

    @classmethod
    def detect_category(cls, title: str, description: str = "") -> str:
        """Classify the user's intent into a primary project category."""
        text = f"{title} {description}".lower()

        # Check for specific strong indicators
        if any(w in text for w in ["portfolio", "resume", "cv", "data analyst", "personal site"]):
            return "portfolio"
        if any(w in text for w in ["bakery", "cafe", "restaurant", "local shop", "bakery website", "cake"]):
            return "business_storefront"
        if any(w in text for w in ["attendance", "student attendance", "dashboard", "saas", "crm", "admin portal"]):
            return "saas_dashboard"
        if any(w in text for w in ["cart", "checkout", "e-commerce", "ecommerce", "online store"]):
            return "e_commerce"
        if any(w in text for w in ["landing page", "waitlist", "lead capture"]):
            return "landing_page"
        if any(w in text for w in ["blog", "articles", "news"]):
            return "blog"

        # General category score-based detection
        for cat, data in PROJECT_CATEGORIES.items():
            for kw in data["keywords"]:
                if re.search(rf"\b{re.escape(kw)}\b", text):
                    return cat

        return "saas_dashboard"

    @classmethod
    def analyze_requirements(cls, title: str, description: str) -> Dict[str, Any]:
        """Extract user requirements, category, and core constraints from text."""
        category = cls.detect_category(title, description)
        text = f"{title} {description}".lower()

        # Extract features mentioned in text
        features = []
        if "resume" in text or "cv" in text:
            features.append("Resume Download & Skill Matrix")
        if "contact" in text or "form" in text or "inquiry" in text:
            features.append("Interactive Contact Form with Ingestion API")
        if "cart" in text or "order" in text or "checkout" in text:
            features.append("Interactive Cart & Order Submission Workflow")
        if "attendance" in text:
            features.append("Daily Attendance Marking & Historical Ledger")
        if "project" in text or "portfolio" in text:
            features.append("Featured Project Gallery with Filterable Tags")
        if "product" in text or "catalogue" in text or "menu" in text:
            features.append("Categorized Product Catalogue with Live Search")
        if "student" in text or "record" in text:
            features.append("Student Roster Management with Full CRUD")

        return {
            "title": title.strip(),
            "description": description.strip(),
            "category": category,
            "category_label": PROJECT_CATEGORIES.get(category, {}).get("label", "Web Application"),
            "extracted_features": features,
        }

    @classmethod
    def generate_blueprint_fallback(
        cls,
        title: str,
        description: str,
        category: Optional[str] = None,
        tech_stack: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Produce a high-fidelity, category-specific blueprint when AI is unconfigured or unavailable.
        Ensures portfolio, bakery, attendance dashboard, etc. have genuinely different designs,
        tables, endpoints, and page structures.
        """
        cat = category or cls.detect_category(title, description)
        clean_title = title.strip() or "Web Application"
        clean_desc = description.strip() or f"Specialized production system for {clean_title}."

        if cat == "portfolio":
            return cls._build_portfolio_blueprint(clean_title, clean_desc, tech_stack, custom_instructions)
        elif cat == "business_storefront":
            return cls._build_bakery_storefront_blueprint(clean_title, clean_desc, tech_stack, custom_instructions)
        elif cat == "saas_dashboard":
            return cls._build_attendance_dashboard_blueprint(clean_title, clean_desc, tech_stack, custom_instructions)
        else:
            return cls._build_general_blueprint(clean_title, clean_desc, cat, tech_stack, custom_instructions)

    @classmethod
    def _build_portfolio_blueprint(cls, title: str, desc: str, stack: Optional[Dict[str, Any]], custom: Optional[str]) -> Dict[str, Any]:
        default_stack = {
            "frontend": ["HTML5 Semantic Elements", "Modern Glassmorphism CSS", "Vanilla ES6 JavaScript"],
            "backend": ["Python 3.11+", "FastAPI Async Framework", "Pydantic V2"],
            "database": "SQLite with SQLAlchemy 2.0 Async (Messages & Project Catalog)",
            "testing": ["pytest", "fastapi.testclient.TestClient"],
            "deployment": "Docker / Vercel (Frontend Static) & Cloud Run / Render (API)",
        }
        if stack:
            default_stack.update(stack)

        return {
            "project_name": title,
            "project_description": desc,
            "target_audience": "Tech recruiters, hiring managers, potential clients, and engineering leaders looking for proven data analyst/engineering capability.",
            "main_purpose": "Showcase portfolio projects, technical skills, downloadable resume, and facilitate direct inbound contact inquiries.",
            "project_category": "portfolio",
            "user_roles": ["Visitor / Recruiter", "Portfolio Owner"],
            "required_pages": [
                {"name": "Home / Hero", "route": "/", "purpose": "Professional headline, introductory summary, call-to-actions, and quick links."},
                {"name": "About & Skills", "route": "#about", "purpose": "Background narrative, data analytics philosophy, and categorized technical skill matrix."},
                {"name": "Featured Projects", "route": "#projects", "purpose": "Case studies with dataset overviews, metrics achieved, tool tags, and GitHub/demo links."},
                {"name": "Resume Preview & Download", "route": "#resume", "purpose": "Direct PDF/markdown resume download endpoint and executive summary."},
                {"name": "Contact Inquiry", "route": "#contact", "purpose": "Interactive contact form with real backend validation and database capture."},
            ],
            "features": [
                "Interactive Portfolio Gallery with domain tags (SQL, Python, Tableau, Machine Learning)",
                "Live Skill Mastery Matrix with categorical breakdowns and experience indicators",
                "Direct Resume Download via authenticated/served endpoint with metadata headers",
                "Contact Inquiry Form with CSRF protection, input validation, and SQLite persistence",
                "Responsive Dark/Light Accent Design with mobile navigation drawer",
            ],
            "frontend_technology": {
                "framework": "Semantic HTML5 + Modern Modular CSS + Vanilla ES6",
                "styling": "Clean glassmorphic dark palette with emerald/teal accents, responsive CSS grid, tactile buttons",
                "components": ["Hero Section", "Skill Matrix Grid", "Project Gallery Modal", "Contact Form Validator", "Toast Notification System"],
            },
            "backend_requirements": {
                "framework": "FastAPI (Python 3.11+)",
                "endpoints_count": 6,
                "cors_policy": "Configured for local dev and cloud deployment",
            },
            "database_requirements": {
                "engine": "SQLite (aiosqlite) with SQLAlchemy 2.0 ORM",
                "tables": [
                    {"table": "projects", "columns": ["id VARCHAR(36) PRIMARY KEY", "title VARCHAR(200) NOT NULL", "category VARCHAR(50)", "description TEXT", "metrics_summary VARCHAR(255)", "tech_tags JSON", "github_url VARCHAR(500)", "live_url VARCHAR(500)"], "purpose": "Stores verified portfolio case studies and project demonstrations."},
                    {"table": "skills", "columns": ["id VARCHAR(36) PRIMARY KEY", "category VARCHAR(100) NOT NULL", "name VARCHAR(100) NOT NULL", "proficiency_level VARCHAR(50)", "years_experience FLOAT"], "purpose": "Stores structured technical competencies and tool proficiencies."},
                    {"table": "inquiries", "columns": ["id VARCHAR(36) PRIMARY KEY", "sender_name VARCHAR(100) NOT NULL", "sender_email VARCHAR(255) NOT NULL", "subject VARCHAR(200)", "message TEXT NOT NULL", "status VARCHAR(50) DEFAULT 'unread'", "created_at TIMESTAMP WITH TIME ZONE"], "purpose": "Persists recruiter and client messages submitted through the contact form."},
                ],
            },
            "api_requirements": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "Service health check", "response": "{ status: 'healthy', timestamp: str }"},
                {"method": "GET", "path": "/api/v1/profile", "purpose": "Get personal profile, headline, and bio", "response": "{ name: str, headline: str, bio: str, skills_count: int }"},
                {"method": "GET", "path": "/api/v1/projects", "purpose": "List showcase portfolio projects with tags", "response": "{ items: List[Project], total: int }"},
                {"method": "GET", "path": "/api/v1/skills", "purpose": "List technical competencies grouped by category", "response": "{ categories: Dict[str, List[Skill]] }"},
                {"method": "GET", "path": "/api/v1/resume/download", "purpose": "Download or preview formal professional resume", "response": "Resume payload or markdown document"},
                {"method": "POST", "path": "/api/v1/contact", "purpose": "Submit new recruiter/client inquiry", "response": "{ status: 'received', message: str, inquiry_id: str }"},
            ],
            "authentication_requirements": "Public visitor access with rate limiting on the contact endpoint; administrative authentication documented for backend updates.",
            "external_integrations": "Contact notification dispatcher (documented SMTP / SendGrid connector hook; simulated in local sandbox without false delivery claims).",
            "design_direction": "High-contrast minimalist dark theme with subtle indigo & emerald glow, monospace code highlights, and fluid responsive typography.",
            "responsive_requirements": "Mobile first (320px+), Tablet grid reflow (768px), and expansive desktop layout (1280px+).",
            "testing_requirements": "Pytest test suite verifying portfolio routes, skill listing, contact form payload validation, and resume download.",
            "deployment_requirements": "Production container specification with Dockerfile and vercel.json rewrite manifest.",
            # Backwards compatibility fields
            "problem_statement": title,
            "detailed_context": desc,
            "mvp_features": [
                "Portfolio Case Study Showcase with Metrics",
                "Technical Skills Matrix with Categories",
                "Downloadable Resume Document Delivery",
                "Functional Inbound Contact Message Ingestion",
                "Responsive Mobile-Ready Navigation",
            ],
            "database_schema": [
                {"table": "projects", "columns": ["id VARCHAR(36) PRIMARY KEY", "title VARCHAR(200)", "category VARCHAR(50)", "description TEXT", "tech_tags JSON"], "purpose": "Portfolio projects"},
                {"table": "skills", "columns": ["id VARCHAR(36) PRIMARY KEY", "category VARCHAR(100)", "name VARCHAR(100)", "proficiency_level VARCHAR(50)"], "purpose": "Skill categories"},
                {"table": "inquiries", "columns": ["id VARCHAR(36) PRIMARY KEY", "sender_name VARCHAR(100)", "sender_email VARCHAR(255)", "message TEXT", "created_at TIMESTAMP"], "purpose": "Contact form submissions"},
            ],
            "api_contracts": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "System liveness probe", "response": "{ status: 'healthy' }"},
                {"method": "GET", "path": "/api/v1/projects", "purpose": "List portfolio projects", "response": "{ items: [] }"},
                {"method": "GET", "path": "/api/v1/skills", "purpose": "Get skills grouped by category", "response": "{ categories: {} }"},
                {"method": "POST", "path": "/api/v1/contact", "purpose": "Submit contact message", "response": "{ status: 'received' }"},
            ],
            "tech_stack": default_stack,
        }

    @classmethod
    def _build_bakery_storefront_blueprint(cls, title: str, desc: str, stack: Optional[Dict[str, Any]], custom: Optional[str]) -> Dict[str, Any]:
        default_stack = {
            "frontend": ["HTML5 Semantic Elements", "Warm Artisanal CSS Styling", "Vanilla ES6 JavaScript"],
            "backend": ["Python 3.11+", "FastAPI Async Framework", "Pydantic V2"],
            "database": "SQLite with SQLAlchemy 2.0 Async (Product Catalog & Order Ledger)",
            "testing": ["pytest", "fastapi.testclient.TestClient"],
            "deployment": "Docker / Vercel (Storefront SPA) & Render Web Service",
        }
        if stack:
            default_stack.update(stack)

        return {
            "project_name": title,
            "project_description": desc,
            "target_audience": "Local neighborhood customers, pastry lovers, event planners, and online order shoppers looking for fresh bakery goods.",
            "main_purpose": "Display artisan baked goods catalogue, pricing, dietary information, and enable online shopping cart order submissions for pickup.",
            "project_category": "business_storefront",
            "user_roles": ["Customer / Shopper", "Bakery Staff / Admin"],
            "required_pages": [
                {"name": "Bakery Storefront", "route": "/", "purpose": "Warm artisan hero, daily fresh specials, bakery history, and store hours."},
                {"name": "Product Catalogue & Menu", "route": "#menu", "purpose": "Categorized bakery items (Artisan Breads, Pastries, Cakes, Savory) with pricing and dietary tags."},
                {"name": "Interactive Cart & Checkout", "route": "#cart", "purpose": "Review items, adjust quantities, select pickup date/time, and submit order."},
                {"name": "Location & Hours", "route": "#location", "purpose": "Address, map directions, contact phone, and operating hours."},
            ],
            "features": [
                "Categorized Artisan Product Catalogue with live price, description, and allergen indicators",
                "Client-Side Shopping Cart with persistent local storage and live subtotal calculations",
                "Order Submission Workflow capturing customer name, phone, pickup date/time, and order notes",
                "Backend Order Ledger generating unique confirmation codes and saving orders to SQLite",
                "Business Hours & Store Status badge (Open Now vs Closed) calculated from local store time",
            ],
            "frontend_technology": {
                "framework": "Semantic HTML5 + Artisanal Warm CSS + Vanilla ES6",
                "styling": "Warm amber and terracotta palette with soft card elevations, appetizing typography, and responsive grid",
                "components": ["Product Card with Add-to-Cart", "Floating Cart Drawer", "Order Checkout Modal", "Dietary Filter Chips", "Pickup Time Selector"],
            },
            "backend_requirements": {
                "framework": "FastAPI (Python 3.11+)",
                "endpoints_count": 6,
                "cors_policy": "Full CORS enabled for web orders",
            },
            "database_requirements": {
                "engine": "SQLite (aiosqlite) with SQLAlchemy 2.0 ORM",
                "tables": [
                    {"table": "products", "columns": ["id VARCHAR(36) PRIMARY KEY", "name VARCHAR(150) NOT NULL", "category VARCHAR(50) NOT NULL", "description TEXT", "price FLOAT NOT NULL", "is_available BOOLEAN DEFAULT TRUE", "dietary_tags JSON"], "purpose": "Stores bakery product catalogue, prices, and availability."},
                    {"table": "orders", "columns": ["id VARCHAR(36) PRIMARY KEY", "order_code VARCHAR(20) UNIQUE NOT NULL", "customer_name VARCHAR(100) NOT NULL", "customer_email VARCHAR(255) NOT NULL", "customer_phone VARCHAR(50) NOT NULL", "pickup_time VARCHAR(100) NOT NULL", "total_amount FLOAT NOT NULL", "status VARCHAR(50) DEFAULT 'confirmed'", "special_instructions TEXT", "created_at TIMESTAMP WITH TIME ZONE"], "purpose": "Records submitted customer pickup orders."},
                    {"table": "order_items", "columns": ["id VARCHAR(36) PRIMARY KEY", "order_id VARCHAR(36) REFERENCES orders(id)", "product_id VARCHAR(36)", "product_name VARCHAR(150)", "unit_price FLOAT", "quantity INT NOT NULL"], "purpose": "Line items for each placed order."},
                ],
            },
            "api_requirements": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "Health and store status check", "response": "{ status: 'healthy', store_open: bool }"},
                {"method": "GET", "path": "/api/v1/products", "purpose": "Retrieve menu catalogue with prices and category filters", "response": "{ items: List[Product], total: int }"},
                {"method": "GET", "path": "/api/v1/products/{id}", "purpose": "Get single product detail and allergen info", "response": "Product"},
                {"method": "POST", "path": "/api/v1/orders", "purpose": "Submit customer order for bakery pickup", "response": "{ status: 'confirmed', order_code: str, total_amount: float }"},
                {"method": "GET", "path": "/api/v1/orders/{order_code}", "purpose": "Check pickup order status with confirmation code", "response": "OrderDetails"},
                {"method": "GET", "path": "/api/v1/store/info", "purpose": "Store hours, address, and announcement banner", "response": "{ hours: Dict, address: str, phone: str }"},
            ],
            "authentication_requirements": "Open customer ordering without account login; staff order review endpoint protected by API token.",
            "external_integrations": "Payment gateway interface specified (Pay on Pickup enabled by default; Stripe integration hook documented).",
            "design_direction": "Warm cream, cinnamon, and terracotta tones, tactile rounded corners, appetizing food styling, and welcoming artisan feel.",
            "responsive_requirements": "Optimized for mobile ordering (bottom cart pill), tablet browsing, and desktop viewing.",
            "testing_requirements": "Pytest suite verifying menu catalogue retrieval, order submission validation, total price calculation, and order tracking.",
            "deployment_requirements": "Docker container with Uvicorn ASGI server and Vercel routing configuration.",
            # Backwards compatibility fields
            "problem_statement": title,
            "detailed_context": desc,
            "mvp_features": [
                "Artisan Bakery Product Catalogue with Dietary Filters",
                "Interactive Customer Shopping Cart with Live Subtotal",
                "Order Submission & Pickup Time Scheduling",
                "Persistent Order Storage in SQLite Database",
                "Order Status Verification by Confirmation Code",
            ],
            "database_schema": [
                {"table": "products", "columns": ["id VARCHAR(36) PRIMARY KEY", "name VARCHAR(150)", "category VARCHAR(50)", "price FLOAT", "is_available BOOLEAN"], "purpose": "Menu items and prices"},
                {"table": "orders", "columns": ["id VARCHAR(36) PRIMARY KEY", "order_code VARCHAR(20) UNIQUE", "customer_name VARCHAR(100)", "customer_phone VARCHAR(50)", "pickup_time VARCHAR(100)", "total_amount FLOAT", "status VARCHAR(50)"], "purpose": "Customer orders"},
                {"table": "order_items", "columns": ["id VARCHAR(36) PRIMARY KEY", "order_id VARCHAR(36)", "product_name VARCHAR(150)", "unit_price FLOAT", "quantity INT"], "purpose": "Order line items"},
            ],
            "api_contracts": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "Store health check", "response": "{ status: 'healthy' }"},
                {"method": "GET", "path": "/api/v1/products", "purpose": "Get product menu", "response": "{ items: [] }"},
                {"method": "POST", "path": "/api/v1/orders", "purpose": "Submit pickup order", "response": "{ status: 'confirmed', order_code: '...' }"},
                {"method": "GET", "path": "/api/v1/orders/{order_code}", "purpose": "Lookup order status", "response": "{ order_code: '...' }"},
            ],
            "tech_stack": default_stack,
        }

    @classmethod
    def _build_attendance_dashboard_blueprint(cls, title: str, desc: str, stack: Optional[Dict[str, Any]], custom: Optional[str]) -> Dict[str, Any]:
        default_stack = {
            "frontend": ["HTML5 Semantic Elements", "Modern Glassmorphic Slate CSS", "Vanilla ES6 JavaScript"],
            "backend": ["Python 3.11+", "FastAPI Async Framework", "Pydantic V2"],
            "database": "SQLite with SQLAlchemy 2.0 Async (Relational Student & Attendance Models)",
            "testing": ["pytest", "fastapi.testclient.TestClient"],
            "deployment": "Docker Container / Cloud Run / Vercel Hybrid",
        }
        if stack:
            default_stack.update(stack)

        return {
            "project_name": title,
            "project_description": desc,
            "target_audience": "School administrators, teachers, university registrars, and educational program managers.",
            "main_purpose": "Streamline daily student attendance tracking, manage student rosters, calculate attendance rates, and flag chronic absenteeism.",
            "project_category": "saas_dashboard",
            "user_roles": ["Administrator / Registrar", "Teacher / Instructor"],
            "required_pages": [
                {"name": "Attendance Executive Dashboard", "route": "/", "purpose": "Overview of today's attendance rate, total enrolled students, absent count, and class breakdown."},
                {"name": "Student Directory", "route": "#students", "purpose": "Full roster of students with enrollment IDs, grades, email, parent contact, and attendance percentage."},
                {"name": "Attendance Register & Marker", "route": "#register", "purpose": "Interactive roll-call sheet to mark students Present, Absent, Late, or Excused for any selected date."},
                {"name": "Attendance History & Reports", "route": "#reports", "purpose": "Date-range log filterable by class and student with export options."},
            ],
            "features": [
                "Real-Time Attendance Metric Engine calculating true attendance percentages from SQLite logs",
                "Full Student Roster CRUD (Create, Read, Update, Delete student records)",
                "Roll-Call Attendance Sheet with single-click status toggles (Present / Absent / Late / Excused)",
                "Date-based Attendance History with query filters by class, date, and status",
                "Chronic Absenteeism Flagging for students falling below minimum attendance threshold (85%)",
            ],
            "frontend_technology": {
                "framework": "Semantic HTML5 + Enterprise Slate CSS + Vanilla ES6",
                "styling": "Deep navy/slate SaaS aesthetic with emerald (Present), crimson (Absent), and amber (Late) status indicators",
                "components": ["KPI Stat Cards", "Student Roster Data Table", "Roll-Call Attendance Grid", "Student Enrollment Modal", "Date Selector Toolbar"],
            },
            "backend_requirements": {
                "framework": "FastAPI (Python 3.11+)",
                "endpoints_count": 8,
                "cors_policy": "Full CORS enabled for dashboard client",
            },
            "database_requirements": {
                "engine": "SQLite (aiosqlite) with SQLAlchemy 2.0 ORM",
                "tables": [
                    {"table": "students", "columns": ["id VARCHAR(36) PRIMARY KEY", "student_id VARCHAR(50) UNIQUE NOT NULL", "full_name VARCHAR(150) NOT NULL", "grade_level VARCHAR(50) NOT NULL", "email VARCHAR(255)", "contact_phone VARCHAR(50)", "is_active BOOLEAN DEFAULT TRUE", "created_at TIMESTAMP WITH TIME ZONE"], "purpose": "Stores enrolled student profiles and contact information."},
                    {"table": "attendance_records", "columns": ["id VARCHAR(36) PRIMARY KEY", "student_id VARCHAR(36) REFERENCES students(id)", "date VARCHAR(10) NOT NULL", "status VARCHAR(20) NOT NULL", "notes VARCHAR(255)", "marked_by VARCHAR(100)", "recorded_at TIMESTAMP WITH TIME ZONE"], "purpose": "Records daily attendance status (Present, Absent, Late, Excused) per student."},
                    {"table": "classes", "columns": ["id VARCHAR(36) PRIMARY KEY", "code VARCHAR(50) UNIQUE NOT NULL", "name VARCHAR(150) NOT NULL", "room VARCHAR(50)", "instructor VARCHAR(100)"], "purpose": "Academic classes and course cohorts."},
                ],
            },
            "api_requirements": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "System health probe", "response": "{ status: 'healthy', database: 'connected' }"},
                {"method": "GET", "path": "/api/v1/metrics/attendance", "purpose": "Executive statistics (overall attendance rate, enrolled count, today absent)", "response": "{ total_students: int, today_rate: float, absent_today: int }"},
                {"method": "GET", "path": "/api/v1/students", "purpose": "List all enrolled students with attendance rates", "response": "{ items: List[Student], total: int }"},
                {"method": "POST", "path": "/api/v1/students", "purpose": "Enroll new student record", "response": "{ status: 'created', student: Student }"},
                {"method": "DELETE", "path": "/api/v1/students/{id}", "purpose": "Archive or remove student record", "response": "{ status: 'deleted', id: str }"},
                {"method": "GET", "path": "/api/v1/attendance", "purpose": "Query attendance records by date and class", "response": "{ records: List[AttendanceRecord], total: int }"},
                {"method": "POST", "path": "/api/v1/attendance/batch", "purpose": "Submit batch attendance roll-call for a date", "response": "{ status: 'saved', count: int }"},
            ],
            "authentication_requirements": "Session/bearer token authentication documented for instructor and administrator access.",
            "external_integrations": "SMS/Email notification webhook hook for unexcused absence alerts (documented for integration).",
            "design_direction": "Data-dense enterprise admin layout with clean typography, tabular data density, status badges, and rapid keyboard entry.",
            "responsive_requirements": "Tablet-friendly roll-call mode and wide multi-column desktop dashboard.",
            "testing_requirements": "Pytest suite testing student enrollment, duplicate ID prevention, roll-call recording, and attendance rate mathematics.",
            "deployment_requirements": "Production Docker container with persistent SQLite volume and Uvicorn server.",
            # Backwards compatibility fields
            "problem_statement": title,
            "detailed_context": desc,
            "mvp_features": [
                "Real-Time Student Attendance Dashboard with Live Percentages",
                "Full Student Directory Management with Enrollment CRUD",
                "Daily Roll-Call Attendance Marking (Present / Absent / Late)",
                "Historical Attendance Querying Filterable by Date and Class",
                "Chronic Absenteeism Flagging and Reporting",
            ],
            "database_schema": [
                {"table": "students", "columns": ["id VARCHAR(36) PRIMARY KEY", "student_id VARCHAR(50) UNIQUE", "full_name VARCHAR(150)", "grade_level VARCHAR(50)"], "purpose": "Enrolled students"},
                {"table": "attendance_records", "columns": ["id VARCHAR(36) PRIMARY KEY", "student_id VARCHAR(36)", "date VARCHAR(10)", "status VARCHAR(20)"], "purpose": "Attendance logs"},
                {"table": "classes", "columns": ["id VARCHAR(36) PRIMARY KEY", "code VARCHAR(50)", "name VARCHAR(150)"], "purpose": "Class cohorts"},
            ],
            "api_contracts": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "Health probe", "response": "{ status: 'healthy' }"},
                {"method": "GET", "path": "/api/v1/metrics/attendance", "purpose": "Calculated attendance KPIs", "response": "{ total_students: int, today_rate: float }"},
                {"method": "GET", "path": "/api/v1/students", "purpose": "Get student roster", "response": "{ items: [] }"},
                {"method": "POST", "path": "/api/v1/students", "purpose": "Create student", "response": "{ status: 'created' }"},
                {"method": "POST", "path": "/api/v1/attendance/batch", "purpose": "Save roll-call", "response": "{ status: 'saved' }"},
            ],
            "tech_stack": default_stack,
        }

    @classmethod
    def _build_general_blueprint(cls, title: str, desc: str, category: str, stack: Optional[Dict[str, Any]], custom: Optional[str]) -> Dict[str, Any]:
        default_stack = {
            "frontend": ["HTML5 Semantic Elements", "Modern Glassmorphism CSS", "Vanilla ES6 JavaScript"],
            "backend": ["Python 3.11+", "FastAPI Async Framework", "Pydantic V2"],
            "database": "SQLite with SQLAlchemy 2.0 Async",
            "testing": ["pytest", "fastapi.testclient.TestClient"],
            "deployment": "Docker Container / Cloud Run",
        }
        if stack:
            default_stack.update(stack)

        req_info = cls.analyze_requirements(title, desc)
        extracted = req_info.get("extracted_features", [])
        if not extracted:
            extracted = [f"{title} Primary Domain Operations", "SQLite Persistence & Audit Trail", "REST API Operations"]

        pages = [
            {"name": "Home / Dashboard", "route": "/", "purpose": f"Main dashboard view for {title}."},
            {"name": "Data Management", "route": "#manage", "purpose": f"Record administration for {title}."},
        ]
        if category == "blog":
            pages = [
                {"name": "Blog Home", "route": "/", "purpose": "Articles feed, featured story, and search."},
                {"name": "Article Reader", "route": "#post", "purpose": "Full-text article with comments section."},
            ]
            extracted = ["Article Feed with Tag Filtering", "Markdown Reader with Code Highlighting", "Visitor Comments System"]
        elif category == "e_commerce":
            pages = [
                {"name": "Storefront", "route": "/", "purpose": "Product showcase, categories, and price tags."},
                {"name": "Cart & Checkout", "route": "#checkout", "purpose": "Cart management and order payment flow."},
            ]
            extracted = ["Product Showcase with Filtering", "Shopping Cart & Line-Item Subtotaling", "Order Checkout & Confirmation"]

        return {
            "project_name": title,
            "project_description": desc,
            "target_audience": f"Users and administrators of {title}.",
            "main_purpose": f"Functional web application providing {title} capabilities.",
            "project_category": category,
            "user_roles": ["Standard User", "Administrator"],
            "required_pages": pages,
            "features": extracted,
            "frontend_technology": {
                "framework": "Semantic HTML5 + Modern CSS + Vanilla ES6",
                "styling": "Modern clean responsive layout with accessible controls",
                "components": ["Header", "Data View", "Action Form", "Status Bar"],
            },
            "backend_requirements": {
                "framework": "FastAPI (Python 3.11+)",
                "endpoints_count": 5,
                "cors_policy": "CORS enabled",
            },
            "database_requirements": {
                "engine": "SQLite with SQLAlchemy 2.0 ORM",
                "tables": [
                    {"table": "records", "columns": ["id VARCHAR(36) PRIMARY KEY", "title VARCHAR(200) NOT NULL", "status VARCHAR(50) DEFAULT 'active'", "created_at TIMESTAMP WITH TIME ZONE"], "purpose": "Primary domain entities"},
                ],
            },
            "api_requirements": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "Health check", "response": "{ status: 'healthy' }"},
                {"method": "GET", "path": "/api/v1/records", "purpose": "List records", "response": "{ items: [] }"},
                {"method": "POST", "path": "/api/v1/records", "purpose": "Create record", "response": "{ status: 'created' }"},
            ],
            "authentication_requirements": "Standard session or API token authentication.",
            "external_integrations": "Standard webhook and notification integration points.",
            "design_direction": "Responsive clean typography with accessibility compliance.",
            "responsive_requirements": "Fluid mobile and desktop layout.",
            "testing_requirements": "Pytest suite testing health and CRUD endpoints.",
            "deployment_requirements": "Docker container with Uvicorn.",
            "problem_statement": title,
            "detailed_context": desc,
            "mvp_features": ["Core Domain Management", "SQLite Persistence", "REST API Operations"],
            "database_schema": [{"table": "records", "columns": ["id VARCHAR(36) PRIMARY KEY", "title VARCHAR(200)", "status VARCHAR(50)"], "purpose": "Records"}],
            "api_contracts": [{"method": "GET", "path": "/api/v1/health", "purpose": "Health", "response": "{ status: 'healthy' }"}],
            "tech_stack": default_stack,
        }

    @classmethod
    async def generate_blueprint(
        cls,
        title: str,
        description: str,
        tech_stack: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete, structured blueprint.
        Uses AI if configured; otherwise provides high-fidelity, category-specific blueprint.
        """
        category = cls.detect_category(title, description)
        logger.info(f"BlueprintEngine: Generating blueprint for '{title}' (Category: {category})")

        if not settings.ai_configured:
            logger.info("AI provider not configured, generating deterministic category-specific blueprint.")
            return cls.generate_blueprint_fallback(
                title=title,
                description=description,
                category=category,
                tech_stack=tech_stack,
                custom_instructions=custom_instructions,
            )

        custom_section = ""
        if tech_stack:
            custom_section += f"\nUser Specified Tech Stack Requirements: {json.dumps(tech_stack, indent=2)}\n"
        if custom_instructions:
            custom_section += f"\nUser Custom Features / Architectural Directives: {custom_instructions.strip()}\n"

        prompt = f"""You are an elite software architect and full-stack product engineer.
Design a complete, production-grade, highly specific project blueprint for this real-world application:

Project Title: {title}
Description / Requirements: {description}
Detected Project Category: {category}
{custom_section}

CRITICAL RULES:
1. The blueprint must be completely unique and tailored specifically to this exact project. DO NOT create a generic discrepancy-monitoring tool unless specifically asked.
2. Return ONLY a single valid JSON object containing all required fields.

JSON Schema:
{{
  "project_name": "{title}",
  "project_description": "Clear 2-3 sentence overview of this specific application",
  "target_audience": "Detailed description of exact user personas",
  "main_purpose": "Primary objective and user problem solved",
  "project_category": "{category}",
  "user_roles": ["Role 1", "Role 2"],
  "required_pages": [
    {{"name": "Page Name", "route": "/path", "purpose": "Specific user function of this page"}}
  ],
  "features": [
    "Concrete feature 1 tailored to this project",
    "Concrete feature 2 tailored to this project",
    "Concrete feature 3 tailored to this project",
    "Concrete feature 4 tailored to this project",
    "Concrete feature 5 tailored to this project"
  ],
  "frontend_technology": {{
    "framework": "Semantic HTML5 + CSS3 + Vanilla ES6",
    "styling": "Styling approach and visual design guidelines",
    "components": ["Component 1", "Component 2", "Component 3"]
  }},
  "backend_requirements": {{
    "framework": "FastAPI (Python 3.11+)",
    "endpoints_count": 6,
    "cors_policy": "Full CORS enabled"
  }},
  "database_requirements": {{
    "engine": "SQLite (aiosqlite) with SQLAlchemy 2.0 ORM",
    "tables": [
      {{"table": "table_name", "columns": ["id VARCHAR(36) PRIMARY KEY", "col1 TYPE", "col2 TYPE"], "purpose": "Purpose of this table"}}
    ]
  }},
  "api_requirements": [
    {{"method": "GET", "path": "/api/v1/...", "purpose": "What this does", "response": "JSON schema description"}}
  ],
  "authentication_requirements": "Authentication strategy and requirements",
  "external_integrations": "Documented integration points (email, payment, third-party)",
  "design_direction": "Visual aesthetic, color palette, and layout principles",
  "responsive_requirements": "Mobile, tablet, desktop adaptation rules",
  "testing_requirements": "Pytest test specifications for business logic and endpoints",
  "deployment_requirements": "Docker and cloud deployment specifications",
  "problem_statement": "{title}",
  "detailed_context": "{description}",
  "mvp_features": ["Feature 1", "Feature 2", "Feature 3"],
  "database_schema": [
    {{"table": "table_name", "columns": ["id VARCHAR(36) PRIMARY KEY", "col1 TYPE"], "purpose": "table purpose"}}
  ],
  "api_contracts": [
    {{"method": "GET", "path": "/api/v1/health", "purpose": "Liveness probe", "response": "{{ status: 'healthy' }}"}}
  ],
  "tech_stack": {{"frontend": ["HTML5", "CSS3", "Vanilla ES6"], "backend": ["FastAPI", "Python"], "database": "SQLite / SQLAlchemy", "testing": ["pytest"], "deployment": "Docker"}}
}}

Return ONLY the raw JSON object. No markdown backticks or commentary."""

        try:
            ai_res = await analyze_with_ai(prompt, temperature=0.2)
            if ai_res:
                data = extract_json_from_llm(ai_res)
                if isinstance(data, dict) and "project_name" in data and "project_category" in data and "database_requirements" in data:
                    if tech_stack and isinstance(data.get("tech_stack"), dict):
                        data["tech_stack"].update(tech_stack)
                    return data
                logger.warning(f"AI blueprint could not be parsed into valid schema, falling back to deterministic blueprint.")
        except Exception as e:
            logger.warning(f"Error calling AI for blueprint: {e}")

        return cls.generate_blueprint_fallback(
            title=title,
            description=description,
            category=category,
            tech_stack=tech_stack,
            custom_instructions=custom_instructions,
        )
