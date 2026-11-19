"""
ProblemPilot AI — Project Blueprint & Architecture Architect
Generates comprehensive, non-generic project blueprints, system architectures,
database schemas, API contracts, interview preparation guides, and resume bullets.
"""
import json
import logging
from typing import Dict, Any, Optional

from backend.config import settings
from backend.services.research_service import analyze_with_ai, extract_json_from_llm

logger = logging.getLogger(__name__)


class ProjectArchitect:
    """
    Synthesizes tailored software blueprints from validated problem opportunities.
    """

    @staticmethod
    def generate_fallback_blueprint(problem_title: str, problem_desc: str, tech_stack: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a rigorous, complete architectural specification when LLM is unavailable.
        Dynamically adapts architecture layers, schemas, and interview questions to the tech stack.
        """
        clean_title = problem_title.replace("’", "'").strip()
        stack = tech_stack or {
            "frontend": ["HTML5 Semantic Elements", "Modern CSS Glassmorphism", "Vanilla ES6 JavaScript"],
            "backend": ["Python 3.11+", "FastAPI Async Framework", "Pydantic V2 Models"],
            "database": "SQLite (Development) / PostgreSQL with SQLAlchemy 2.0 Async ORM",
            "testing": ["pytest", "pytest-asyncio", "httpx TestClient"],
            "deployment": "Docker / Vercel (Frontend) & Render / Railway (Backend API)",
        }

        fe_desc = ", ".join(stack.get("frontend", [])) if isinstance(stack.get("frontend"), list) else str(stack.get("frontend", "Web SPA Client"))
        be_desc = ", ".join(stack.get("backend", [])) if isinstance(stack.get("backend"), list) else str(stack.get("backend", "FastAPI Async Application"))
        db_desc = str(stack.get("database", "Relational Database Engine with Transactional Integrity"))

        return {
            "problem_statement": clean_title,
            "detailed_context": problem_desc or f"Production-ready architecture designed to resolve {clean_title}.",
            "target_users": "Engineering teams, operations leads, and technical founders needing reliable automated solutions.",
            "mvp_features": [
                f"Real-time {clean_title} Telemetry Dashboard with live monitoring.",
                "Automated Anomaly Detection & Discrepancy Flagging Engine.",
                "RESTful API contracts for data ingestion, querying, and verification audit trails.",
                "Configurable Webhook & Event Notification Dispatcher.",
                "CSV and JSON export capabilities for compliance and analysis.",
            ],
            "functional_requirements": [
                "System must process incoming records within 200ms with non-blocking async I/O.",
                "Discrepancies must be flagged with severity tags (Low, Medium, Critical).",
                "Audit logs must record all state modifications with UTC timestamps.",
                "User must be able to filter, search, and resolve identified issues via the UI.",
            ],
            "non_functional_requirements": [
                "Security: JWT bearer authentication, input sanitization, and role-based permissions.",
                "Performance: Asynchronous I/O handling high concurrent workloads with sub-50ms p95 latency.",
                "Maintainability: Modular clean architecture separating routes, services, schemas, and models.",
                "Reliability: Graceful degradation and fallback handlers on upstream service timeouts.",
            ],
            "architecture": {
                "pattern": "Layered Micro-modular Clean Architecture",
                "frontend_layer": f"Client Layer ({fe_desc}): High-performance reactive user interface communicating over JSON REST APIs.",
                "api_gateway_layer": f"API & Gateway Layer ({be_desc}): Asynchronous service boundary with CORS middleware, rate limiters, and error interceptors.",
                "service_layer": "Domain Logic Layer: Validation services, anomaly scoring calculations, and transactional persistence bridges.",
                "data_layer": f"Persistence Layer ({db_desc}): Schema management with transactional integrity and indexing.",
            },
            "database_schema": [
                {
                    "table": "entities",
                    "columns": [
                        "id VARCHAR(36) PRIMARY KEY",
                        "title VARCHAR(255) NOT NULL",
                        "status VARCHAR(50) DEFAULT 'active'",
                        "metadata JSON",
                        "created_at TIMESTAMP WITH TIME ZONE",
                        "updated_at TIMESTAMP WITH TIME ZONE",
                    ],
                    "indexes": ["idx_entities_status", "idx_entities_created_at"],
                    "purpose": "Stores core business entities being tracked or reconciled.",
                },
                {
                    "table": "discrepancies",
                    "columns": [
                        "id VARCHAR(36) PRIMARY KEY",
                        "entity_id VARCHAR(36) REFERENCES entities(id)",
                        "severity VARCHAR(20) NOT NULL",
                        "description TEXT NOT NULL",
                        "resolved BOOLEAN DEFAULT FALSE",
                        "detected_at TIMESTAMP WITH TIME ZONE",
                    ],
                    "indexes": ["idx_discrepancies_resolved"],
                    "purpose": "Stores detected issues, variances, or anomalies with resolution tracking.",
                },
                {
                    "table": "audit_events",
                    "columns": [
                        "id VARCHAR(36) PRIMARY KEY",
                        "event_type VARCHAR(100) NOT NULL",
                        "details JSON",
                        "created_at TIMESTAMP WITH TIME ZONE",
                    ],
                    "indexes": ["idx_audit_events_created_at"],
                    "purpose": "Immutable chronological ledger of all automated and manual actions.",
                },
            ],
            "api_contracts": [
                {"method": "GET", "path": "/api/v1/health", "purpose": "System liveness probe and health check verification.", "response": "{ status: 'healthy', timestamp: str }"},
                {"method": "GET", "path": "/api/v1/metrics/summary", "purpose": "Quantitative statistics for executive dashboard.", "response": "{ total_events: int, open_anomalies: int, health_score: float }"},
                {"method": "GET", "path": "/api/v1/entities", "purpose": "List tracked records with pagination and status filters.", "response": "{ items: [], total: int }"},
                {"method": "POST", "path": "/api/v1/entities", "purpose": "Ingest and validate new entity record.", "response": "{ id: str, status: 'created' }"},
                {"method": "GET", "path": "/api/v1/discrepancies", "purpose": "Retrieve active unacknowledged anomalies.", "response": "{ discrepancies: [] }"},
                {"method": "POST", "path": "/api/v1/discrepancies/{id}/resolve", "purpose": "Mark an anomaly as investigated and resolved.", "response": "{ status: 'resolved' }"},
            ],
            "tech_stack": stack,
            "testing_plan": [
                "Unit Tests: Model schema validation, business metric formulas, and edge case parsers.",
                "Integration Tests: Full HTTP request-response flow via AsyncClient ASGI transport.",
                "End-to-End Smoke Tests: SPA static asset serving and live API connectivity check.",
            ],
            "interview_preparation": [
                {
                    "question": f"Why is {be_desc} the right architectural choice for {clean_title}?",
                    "answer": f"{be_desc} provides native asynchronous coroutines (async/await) which prevent I/O blocking when communicating with databases or external APIs. Paired with strict data validation, it delivers automatic OpenAPI schema generation, compile-time type validation, and high throughput with minimal boilerplate.",
                },
                {
                    "question": "How do you handle schema drift or corrupted data inputs in this system?",
                    "answer": "Input payloads are strictly validated through schemas before reaching the business layer. Any schema anomalies trigger structured 422 Unprocessable Entity responses logged to the audit ledger rather than causing uncaught runtime exceptions.",
                },
                {
                    "question": "What is the single biggest architectural trade-off made in this design?",
                    "answer": "Choosing a single-node asynchronous architecture over a distributed microservice setup. For an MVP processing thousands of daily events, this eliminates network latency and distributed transaction overhead while remaining trivial to containerize and deploy.",
                },
            ],
            "resume_bullet_points": [
                f"Architected and developed {clean_title}, an asynchronous software system reducing manual reconciliation toil by over 80%.",
                f"Engineered RESTful APIs with {be_desc}, achieving sub-20ms response times for high-throughput anomaly detection.",
                f"Implemented resilient data modeling for {db_desc} with automated migration management and comprehensive indexing.",
                "Established automated CI test pipelines with pytest and ASGI test client, ensuring 100% test coverage on critical business logic.",
            ],
        }

    async def generate_blueprint(
        self,
        problem_title: str,
        problem_desc: str,
        tech_stack: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an AI-driven or high-quality fallback project blueprint,
        tailored to any user-customized tech stack or specific requirements.
        """
        if not settings.ai_configured:
            return self.generate_fallback_blueprint(problem_title, problem_desc, tech_stack=tech_stack)

        custom_section = ""
        if tech_stack:
            custom_section += f"\nUser Specified Tech Stack Requirements: {json.dumps(tech_stack, indent=2)}\n"
        if custom_instructions:
            custom_section += f"\nUser Custom Features / Architectural Directives: {custom_instructions.strip()}\n"

        prompt = f"""You are an elite software architect at Google / Y Combinator.
Design a complete, production-grade project blueprint to solve this real-world problem:

Problem: {problem_title}
Context: {problem_desc}
{custom_section}
CRITICAL INSTRUCTION: You MUST incorporate the user's specified tech stack and custom features directly into your architecture design, database schema, API contracts, and tech_stack block.

Generate a comprehensive JSON document with:
- "problem_statement": Concise problem summary
- "detailed_context": In-depth background
- "target_users": Primary audience
- "mvp_features": List of 5 core MVP features (incorporate user custom features if provided)
- "functional_requirements": 4 concrete functional requirements
- "non_functional_requirements": 4 non-functional specs (latency, security, concurrency)
- "architecture": {{"pattern": "...", "frontend_layer": "...", "api_gateway_layer": "...", "service_layer": "...", "data_layer": "..."}}
- "database_schema": Array of 3 tables, each with "table", "columns" (types included), "indexes", "purpose"
- "api_contracts": Array of 5 endpoints with "method", "path", "purpose", "response"
- "tech_stack": {{"frontend": [...], "backend": [...], "database": "...", "testing": [...], "deployment": "..."}}
- "testing_plan": Array of 3 testing strategies
- "interview_preparation": Array of 3 objects with "question" and "answer"
- "resume_bullet_points": Array of 4 high-impact resume achievement bullets

Return ONLY valid JSON. No markdown backticks."""

        ai_res = await analyze_with_ai(prompt)
        if ai_res:
            data = extract_json_from_llm(ai_res)
            if isinstance(data, dict) and "problem_statement" in data and "database_schema" in data:
                # Guarantee that user tech_stack overrides if provided
                if tech_stack and isinstance(data.get("tech_stack"), dict):
                    data["tech_stack"].update(tech_stack)
                return data
            logger.warning(f"AI blueprint could not be parsed into valid blueprint schema: {ai_res[:150]}")

        return self.generate_fallback_blueprint(problem_title, problem_desc, tech_stack=tech_stack)

