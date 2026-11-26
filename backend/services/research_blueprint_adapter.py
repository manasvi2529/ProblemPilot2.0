"""
Research Blueprint Adapter
Transforms 13-section research reports into rich, evidence-grounded blueprints.
Enforces canonical classification, deterministic SHA-256 blueprint hashing,
experimental hypothesis quarantine, domain-specific schemas, and synthetic data labeling.
"""
import hashlib
import json
import uuid
from typing import Dict, Any, List, Optional
from backend.models.research import ResearchReport


CANONICAL_CLASSIFICATIONS = {
    "verified_fact": "verified_fact",
    "verified": "verified_fact",
    "source_backed": "source_backed",
    "inference": "inference",
    "hypothesis": "hypothesis",
}


def canonicalize_classification(raw_class: Optional[str]) -> str:
    """Safely map raw or legacy classification strings to canonical values."""
    if not raw_class:
        return "inference"
    clean = str(raw_class).strip().lower()
    return CANONICAL_CLASSIFICATIONS.get(clean, "inference")


class ResearchBlueprintAdapter:
    """Translates research validation reports into deep, evidence-traceable project blueprints."""

    def compute_blueprint_hash(self, blueprint_dict: Dict[str, Any]) -> str:
        """
        Compute a deterministic SHA-256 hash of the blueprint specifications
        for backend approval binding and invalidation detection.
        """
        core_spec = {
            "title": blueprint_dict.get("title", ""),
            "domain_entities": blueprint_dict.get("domain_entities", []),
            "domain_workflows": blueprint_dict.get("domain_workflows", []),
            "traceability_matrix": blueprint_dict.get("research_intelligence", {}).get("traceability_matrix", []),
            "experimental_hypotheses": blueprint_dict.get("research_intelligence", {}).get("experimental_hypotheses", []),
        }
        encoded = json.dumps(core_spec, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def build_evidence_traceability_matrix(
        self,
        report: ResearchReport,
        opportunity_index: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Build an exhaustive Evidence Traceability Matrix linking every requirement
        to originating research findings, citations, and canonical claim types.
        """
        matrix = []
        is_insufficient = (getattr(report, "evidence_sufficiency", "moderate") or "").lower() == "insufficient"
        sources = report.sources or []

        # 1. Map customer pain points
        pain_points = report.customer_pain_points or []
        for idx, pp in enumerate(pain_points):
            raw_claim = pp.get("claim_type") or ("hypothesis" if is_insufficient else "source_backed")
            canonical_claim = canonicalize_classification(raw_claim)
            if is_insufficient and canonical_claim != "verified_fact":
                canonical_claim = "hypothesis"

            matched_sources = []
            for s in sources:
                if any(kw in s.get("title", "").lower() or kw in s.get("snippet", "").lower()
                       for kw in pp.get("pain_point", "").lower().split()[:3] if len(kw) > 3):
                    matched_sources.append({
                        "title": s.get("title", "Research Source"),
                        "url": s.get("url", ""),
                        "publisher": s.get("publisher", "Web"),
                        "retrieved_at": s.get("retrieved_at", "2026-11-25"),
                    })

            matrix.append({
                "requirement_id": f"REQ-PP-{idx+1:02d}",
                "feature_name": f"Resolve: {pp.get('pain_point', 'User Friction')[:40]}",
                "category": "core_friction_remedy",
                "originating_finding": pp.get("pain_point", ""),
                "evidence_classification": canonical_claim,
                "confidence_score": 0.50 if canonical_claim == "hypothesis" else 0.85,
                "sources": matched_sources or [{"title": report.title, "url": "", "publisher": "Research Session"}],
                "technical_realization": {
                    "frontend_component": f"{pp.get('pain_point', 'Feature')[:20].title().replace(' ', '')}Module.tsx",
                    "backend_route": f"/api/operations/{pp.get('pain_point', 'feature')[:15].lower().replace(' ', '-')}",
                },
            })

        # 2. Map competitor gaps & differentiators
        competitors = report.competitor_analysis or []
        for idx, comp in enumerate(competitors):
            for g_idx, gap in enumerate(comp.get("weaknesses", []) or comp.get("gaps", []) or []):
                matrix.append({
                    "requirement_id": f"REQ-GAP-{idx+1:02d}-{g_idx+1:02d}",
                    "feature_name": f"Differentiator: {str(gap)[:40]}",
                    "category": "competitor_differentiator",
                    "originating_finding": f"Competitor Gap ({comp.get('name', 'Competitor')}): {gap}",
                    "evidence_classification": "hypothesis" if is_insufficient else "inference",
                    "confidence_score": 0.70,
                    "sources": [{"title": f"Competitive analysis: {comp.get('name', 'Market')}", "url": "", "publisher": "Research Engine"}],
                    "technical_realization": {
                        "frontend_component": "DifferentiatorCard.tsx",
                        "backend_route": "/api/differentiators",
                    },
                })

        return matrix

    def extract_domain_entities(self, report: ResearchReport) -> List[Dict[str, Any]]:
        """
        Derive domain-specific database schemas to prevent generic boilerplate.
        """
        query_text = (report.title + " " + (report.executive_summary or "")).lower()
        entities = []

        if any(w in query_text for w in ["crop", "farm", "agri", "pest", "drone", "harvest", "soil"]):
            entities = [
                {
                    "name": "FieldParcel",
                    "table_name": "field_parcels",
                    "description": "Monitored agricultural parcel and boundary telemetry",
                    "columns": [
                        {"name": "id", "type": "String(36)", "primary_key": True},
                        {"name": "parcel_code", "type": "String(50)", "nullable": False},
                        {"name": "crop_type", "type": "String(100)", "nullable": False},
                        {"name": "acreage", "type": "Float", "nullable": False},
                        {"name": "soil_ph", "type": "Float", "nullable": True},
                        {"name": "ndvi_vigor_score", "type": "Float", "nullable": True},
                    ],
                },
                {
                    "name": "InfestationLog",
                    "table_name": "infestation_logs",
                    "description": "Pest detection logs and targeted spray prescriptions",
                    "columns": [
                        {"name": "id", "type": "String(36)", "primary_key": True},
                        {"name": "parcel_id", "type": "String(36)", "foreign_key": "field_parcels.id"},
                        {"name": "pest_species", "type": "String(100)", "nullable": False},
                        {"name": "severity_pct", "type": "Float", "nullable": False},
                        {"name": "prescription_applied", "type": "String(200)", "nullable": True},
                    ],
                },
            ]
        elif any(w in query_text for w in ["clinical", "trial", "patient", "medical", "disease", "protocol", "cohort"]):
            entities = [
                {
                    "name": "ClinicalProtocol",
                    "table_name": "clinical_protocols",
                    "description": "Trial protocol inclusion/exclusion criteria",
                    "columns": [
                        {"name": "id", "type": "String(36)", "primary_key": True},
                        {"name": "protocol_code", "type": "String(50)", "nullable": False},
                        {"name": "condition_target", "type": "String(200)", "nullable": False},
                        {"name": "phase", "type": "String(20)", "nullable": False},
                        {"name": "biomarker_filter", "type": "String(200)", "nullable": True},
                    ],
                },
                {
                    "name": "PatientCohort",
                    "table_name": "patient_cohorts",
                    "description": "De-identified patient cohorts matched against protocols",
                    "columns": [
                        {"name": "id", "type": "String(36)", "primary_key": True},
                        {"name": "protocol_id", "type": "String(36)", "foreign_key": "clinical_protocols.id"},
                        {"name": "cohort_label", "type": "String(100)", "nullable": False},
                        {"name": "match_score", "type": "Float", "nullable": False},
                        {"name": "consent_status", "type": "String(50)", "nullable": False},
                    ],
                },
            ]
        else:
            # Domain-adaptive fallback based on title keywords
            domain_slug = report.title.split()[0].replace(",", "").capitalize()
            entities = [
                {
                    "name": f"{domain_slug}Record",
                    "table_name": f"{domain_slug.lower()}_records",
                    "description": f"Domain record for {report.title}",
                    "columns": [
                        {"name": "id", "type": "String(36)", "primary_key": True},
                        {"name": "title", "type": "String(200)", "nullable": False},
                        {"name": "status", "type": "String(50)", "nullable": False},
                        {"name": "metric_value", "type": "Float", "nullable": True},
                    ],
                }
            ]
        return entities

    def extract_domain_workflows(self, report: ResearchReport) -> List[Dict[str, Any]]:
        """
        Derive domain-specific API endpoints and operational workflows.
        """
        query_text = (report.title + " " + (report.executive_summary or "")).lower()
        if any(w in query_text for w in ["crop", "farm", "agri", "pest", "drone"]):
            return [
                {
                    "endpoint": "POST /api/parcels/{id}/telemetry-sync",
                    "purpose": "Sync drone multispectral NDVI imagery and compute vigor metrics",
                    "request_body": {"flight_id": "str", "ndvi_samples": "List[float]"},
                    "response": {"vigor_index": "float", "infestation_risk": "str"},
                },
                {
                    "endpoint": "POST /api/prescriptions/generate",
                    "purpose": "Generate targeted pesticide formulation based on infestation log",
                    "request_body": {"parcel_id": "str", "severity_pct": "float"},
                    "response": {"prescription_id": "str", "formulation": "str"},
                },
            ]
        elif any(w in query_text for w in ["clinical", "trial", "patient", "medical"]):
            return [
                {
                    "endpoint": "POST /api/protocols/{id}/screen-patient",
                    "purpose": "Screen de-identified patient record against protocol eligibility",
                    "request_body": {"biomarkers": "List[str]", "age": "int"},
                    "response": {"is_eligible": "bool", "match_confidence": "float"},
                },
                {
                    "endpoint": "GET /api/cohorts/{id}/compliance-audit",
                    "purpose": "Export HIPAA-compliant audit trail of cohort eligibility evaluations",
                    "request_body": {},
                    "response": {"audit_id": "str", "evaluated_count": "int"},
                },
            ]
        else:
            return [
                {
                    "endpoint": "/api/operations/evaluate",
                    "purpose": f"Evaluate operational state for {report.title}",
                    "request_body": {"parameters": "dict"},
                    "response": {"status": "success", "result": "dict"},
                }
            ]

    def generate_synthetic_seed_data(self, report: ResearchReport) -> Dict[str, Any]:
        """
        Generate synthetic development data, explicitly tagged and isolated to prevent
        masquerading as actual verified empirical statistics.
        """
        query_text = (report.title + " " + (report.executive_summary or "")).lower()
        disclaimer = "SYNTHETIC SEED DATA — Generated for local development and workflow demonstration only. Not verified research statistics."

        if any(w in query_text for w in ["crop", "farm", "agri", "pest", "drone"]):
            return {
                "disclaimer": disclaimer,
                "is_synthetic": True,
                "records": {
                    "field_parcels": [
                        {"id": "fp-101", "parcel_code": "PUNJAB-SECTOR-4A", "crop_type": "Wheat (HD-3086)", "acreage": 45.5, "soil_ph": 7.2, "ndvi_vigor_score": 0.78},
                        {"id": "fp-102", "parcel_code": "PUNJAB-SECTOR-4B", "crop_type": "Mustard (Pusa Bold)", "acreage": 28.0, "soil_ph": 6.8, "ndvi_vigor_score": 0.62},
                    ],
                    "infestation_logs": [
                        {"id": "il-201", "parcel_id": "fp-102", "pest_species": "Mustard Aphid (Lipaphis erysimi)", "severity_pct": 18.5, "prescription_applied": "Neem Oil 5% Spray"},
                    ],
                },
            }
        elif any(w in query_text for w in ["clinical", "trial", "patient", "medical"]):
            return {
                "disclaimer": disclaimer,
                "is_synthetic": True,
                "records": {
                    "clinical_protocols": [
                        {"id": "cp-301", "protocol_code": "NCT-RARE-2026", "condition_target": "Fabry Disease (GLA mutation)", "phase": "Phase IIb", "biomarker_filter": "GLA-del-exon3"},
                    ],
                    "patient_cohorts": [
                        {"id": "coh-401", "protocol_id": "cp-301", "cohort_label": "Cohort-Alpha-Enriched", "match_score": 94.2, "consent_status": "eConsent-Verified"},
                    ],
                },
            }
        else:
            return {
                "disclaimer": disclaimer,
                "is_synthetic": True,
                "records": {
                    "demo_records": [
                        {"id": "demo-01", "title": f"Demo sample for {report.title}", "status": "active", "metric_value": 42.0},
                    ],
                },
            }

    async def generate_research_grounded_blueprint(
        self,
        report: ResearchReport,
        opportunity_index: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate complete, evidence-grounded blueprint specification.
        """
        opps = report.identified_opportunities or []
        idx = max(0, min(opportunity_index, len(opps) - 1)) if opps else 0
        selected_opp = opps[idx] if opps else {}

        traceability_matrix = self.build_evidence_traceability_matrix(report, idx)
        domain_entities = self.extract_domain_entities(report)
        domain_workflows = self.extract_domain_workflows(report)
        synthetic_seed = self.generate_synthetic_seed_data(report)

        # Flag experimental hypotheses
        hypotheses = [
            req for req in traceability_matrix
            if req.get("evidence_classification") == "hypothesis"
        ]

        is_fallback = not getattr(report, "used_live_search", False)

        blueprint = {
            "title": selected_opp.get("title") or report.title,
            "version": "1.6.0",
            "framework": "fastapi_react",
            "description": selected_opp.get("proposed_solution") or report.executive_summary,
            "domain_entities": domain_entities,
            "domain_workflows": domain_workflows,
            "research_intelligence": {
                "is_research_backed": True,
                "report_id": report.id,
                "session_id": report.session_id,
                "opportunity_index": idx,
                "used_live_search": getattr(report, "used_live_search", False),
                "is_curated_fallback": is_fallback,
                "fallback_notice": (
                    "[CURATED DEMO DATA: Real search API credentials not configured. Results generated from curated domain simulation. Not live web research.]"
                    if is_fallback else ""
                ),
                "evidence_sufficiency": getattr(report, "evidence_sufficiency", "moderate"),
                "traceability_matrix": traceability_matrix,
                "experimental_hypotheses": hypotheses,
                "has_experimental_hypotheses": len(hypotheses) > 0,
                "synthetic_seed_data": synthetic_seed,
                "citations": [
                    {
                        "title": s.get("title", "Source"),
                        "url": s.get("url", ""),
                        "publisher": s.get("publisher", ""),
                        "publication_date": s.get("publication_date", ""),
                    }
                    for s in (report.sources or [])
                ],
            },
        }

        # Calculate cryptographic hash of proposed blueprint
        blueprint["blueprint_hash"] = self.compute_blueprint_hash(blueprint)
        return blueprint


research_blueprint_adapter = ResearchBlueprintAdapter()
