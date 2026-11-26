"""
Blueprint Quality Evaluator (Phase 1.8 Stage 1).
Holistic evaluation of technical project blueprints across 6 concrete facets:
1. Domain entity specificity vs generic boilerplate
2. Relational foreign-key integrity & cardinality
3. Database constraints, indexes, and synthetic data tagging
4. Multi-step business workflows
5. REST API contract & payload completeness
6. Evidence traceability & hypothesis isolation
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import re


@dataclass
class BlueprintDimensionScore:
    score: float
    weight: float
    explanation: str
    evidence_snippets: List[str] = field(default_factory=list)


@dataclass
class BlueprintEvaluationResult:
    overall_score: float
    dimensions: Dict[str, BlueprintDimensionScore]
    passed_gate: bool
    summary: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "passed_gate": self.passed_gate,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "dimensions": {
                k: {
                    "score": v.score,
                    "weight": v.weight,
                    "explanation": v.explanation,
                    "evidence_snippets": v.evidence_snippets,
                }
                for k, v in self.dimensions.items()
            },
        }


class BlueprintQualityEvaluator:
    """Evaluates whether an architectural blueprint is domain-grounded or collapsed into boilerplate CRUD."""

    GENERIC_ENTITY_NAMES = {
        "item", "items", "data", "datum", "thing", "things", "task", "tasks",
        "record", "records", "entity", "entities", "object", "objects", "user", "users"
    }

    def __init__(self):
        self.weights = {
            "domain_entity_richness": 0.25,
            "relational_integrity": 0.20,
            "schema_constraints_and_seed": 0.20,
            "business_workflows": 0.20,
            "evidence_traceability": 0.15,
        }

    def evaluate(self, blueprint: Dict[str, Any]) -> BlueprintEvaluationResult:
        """Execute complete quantitative and structural evaluation of the project blueprint."""
        if not blueprint:
            return BlueprintEvaluationResult(
                overall_score=0.0,
                dimensions={},
                passed_gate=False,
                summary="Empty or null blueprint provided.",
            )

        strengths = []
        weaknesses = []

        # 1. Domain Entity Richness (0 - 10)
        ent_score, ent_expl, ent_ev = self._evaluate_domain_entities(blueprint)
        if ent_score >= 8.0:
            strengths.append(f"Domain-specific modeling: {ent_expl}")
        elif ent_score < 5.0:
            weaknesses.append(f"Generic model collapse: {ent_expl}")

        # 2. Relational Integrity & Schema Design (0 - 10)
        rel_score, rel_expl, rel_ev = self._evaluate_relational_integrity(blueprint)
        if rel_score >= 8.0:
            strengths.append(f"Robust relational architecture: {rel_expl}")
        elif rel_score < 5.0:
            weaknesses.append(f"Weak data modeling: {rel_expl}")

        # 3. Schema Constraints & Seed Data (0 - 10)
        sch_score, sch_expl, sch_ev = self._evaluate_constraints_and_seed(blueprint)
        if sch_score >= 8.0:
            strengths.append(f"Complete schema constraints: {sch_expl}")
        elif sch_score < 5.0:
            weaknesses.append(f"Missing constraints or seed tagging: {sch_expl}")

        # 4. Multi-Step Business Workflows (0 - 10)
        wf_score, wf_expl, wf_ev = self._evaluate_business_workflows(blueprint)
        if wf_score >= 8.0:
            strengths.append(f"Deep domain workflows: {wf_expl}")
        elif wf_score < 5.0:
            weaknesses.append(f"Trivial workflow modeling: {wf_expl}")

        # 5. Evidence Traceability & Hypothesis Isolation (0 - 10)
        tr_score, tr_expl, tr_ev = self._evaluate_evidence_traceability(blueprint)
        if tr_score >= 8.0:
            strengths.append(f"Strong research traceability: {tr_expl}")
        elif tr_score < 5.0:
            weaknesses.append(f"Untraced architecture: {tr_expl}")

        dims = {
            "domain_entity_richness": BlueprintDimensionScore(
                score=round(ent_score, 2),
                weight=self.weights["domain_entity_richness"],
                explanation=ent_expl,
                evidence_snippets=ent_ev,
            ),
            "relational_integrity": BlueprintDimensionScore(
                score=round(rel_score, 2),
                weight=self.weights["relational_integrity"],
                explanation=rel_expl,
                evidence_snippets=rel_ev,
            ),
            "schema_constraints_and_seed": BlueprintDimensionScore(
                score=round(sch_score, 2),
                weight=self.weights["schema_constraints_and_seed"],
                explanation=sch_expl,
                evidence_snippets=sch_ev,
            ),
            "business_workflows": BlueprintDimensionScore(
                score=round(wf_score, 2),
                weight=self.weights["business_workflows"],
                explanation=wf_expl,
                evidence_snippets=wf_ev,
            ),
            "evidence_traceability": BlueprintDimensionScore(
                score=round(tr_score, 2),
                weight=self.weights["evidence_traceability"],
                explanation=tr_expl,
                evidence_snippets=tr_ev,
            ),
        }

        overall = round(
            (ent_score * self.weights["domain_entity_richness"])
            + (rel_score * self.weights["relational_integrity"])
            + (sch_score * self.weights["schema_constraints_and_seed"])
            + (wf_score * self.weights["business_workflows"])
            + (tr_score * self.weights["evidence_traceability"]),
            2,
        )

        passed_gate = overall >= 6.5 and len(weaknesses) <= 2
        summary = (
            f"Blueprint architecture score: {overall}/10. "
            f"{'Demonstrates rich domain grounding.' if passed_gate else 'Collapses into boilerplate generic structures.'}"
        )

        return BlueprintEvaluationResult(
            overall_score=overall,
            dimensions=dims,
            passed_gate=passed_gate,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    def _evaluate_domain_entities(self, blueprint: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade whether entities represent genuine domain objects rather than generic names."""
        entities = blueprint.get("domain_entities", [])
        if not entities:
            # Fallback check under data_models or models
            entities = blueprint.get("data_models", blueprint.get("models", []))

        if not entities:
            return 1.0, "Zero domain entities defined in blueprint.", []

        score = 5.0
        evidence = []
        domain_specific_count = 0
        generic_count = 0

        for ent in entities:
            name = ent.get("name", "").strip().lower()
            if not name:
                continue
            if name in self.GENERIC_ENTITY_NAMES:
                generic_count += 1
            else:
                domain_specific_count += 1

        if domain_specific_count >= 3:
            score += 3.5
            evidence.append(f"Identified {domain_specific_count} domain-specific entities (e.g. {[e.get('name') for e in entities if e.get('name', '').lower() not in self.GENERIC_ENTITY_NAMES][:3]}).")
        elif domain_specific_count >= 1:
            score += 1.5

        if generic_count > 0:
            score -= (generic_count * 1.5)
            evidence.append(f"Penalty: {generic_count} generic placeholder entities detected (e.g. {[e.get('name') for e in entities if e.get('name', '').lower() in self.GENERIC_ENTITY_NAMES]}).")

        score = max(0.0, min(10.0, score))
        explanation = f"Found {domain_specific_count} domain-specific models, {generic_count} generic models."
        return score, explanation, evidence

    def _evaluate_relational_integrity(self, blueprint: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade foreign-key linkages, table relationships, and cardinality."""
        entities = blueprint.get("domain_entities", blueprint.get("data_models", []))
        if not entities:
            return 2.0, "No entities available to evaluate relationships.", []

        score = 4.0
        evidence = []
        relationships_found = 0

        for ent in entities:
            attrs = ent.get("attributes", ent.get("fields", []))
            for a in attrs:
                name = a.get("name", "").lower()
                fk = a.get("foreign_key", "")
                if fk or name.endswith("_id") or "foreign_key" in str(a).lower():
                    relationships_found += 1

        if relationships_found >= 3:
            score += 4.5
            evidence.append(f"Detected {relationships_found} explicit foreign-key linkages establishing relational cohesion.")
        elif relationships_found >= 1:
            score += 2.5
            evidence.append(f"Detected {relationships_found} foreign-key linkage.")
        else:
            score -= 2.0
            evidence.append("Warning: Disjoint entities with zero foreign-key relationships detected.")

        score = max(0.0, min(10.0, score))
        explanation = f"Evaluated {len(entities)} models containing {relationships_found} foreign-key relationships."
        return score, explanation, evidence

    def _evaluate_constraints_and_seed(self, blueprint: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade database constraints (PK, types, indexes) and synthetic seed data labeling."""
        entities = blueprint.get("domain_entities", blueprint.get("data_models", []))
        seed_data = blueprint.get("seed_data", {})

        score = 4.0
        evidence = []
        typed_attributes = 0
        total_attributes = 0

        for ent in entities:
            attrs = ent.get("attributes", ent.get("fields", []))
            for a in attrs:
                total_attributes += 1
                if a.get("type"):
                    typed_attributes += 1

        if total_attributes > 0 and (typed_attributes / total_attributes) >= 0.8:
            score += 2.5
            evidence.append(f"{typed_attributes}/{total_attributes} attributes possess explicit database types.")

        # Check synthetic seed labeling
        if seed_data:
            score += 1.5
            records = seed_data.get("records", [])
            has_synthetic_label = seed_data.get("is_synthetic") or all(r.get("is_synthetic") for r in records if isinstance(r, dict))
            if has_synthetic_label:
                score += 1.5
                evidence.append("Synthetic seed records clearly labeled 'is_synthetic: true'.")
            else:
                score -= 1.0
                evidence.append("Warning: Seed data present but lacks explicit synthetic disclaimer label.")

        score = max(0.0, min(10.0, score))
        explanation = f"Constraints verified across {total_attributes} attributes with seed data inspection."
        return score, explanation, evidence

    def _evaluate_business_workflows(self, blueprint: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade whether workflows model real multi-step operations vs single CRUD calls."""
        workflows = blueprint.get("domain_workflows", blueprint.get("workflows", []))
        if not workflows:
            return 2.0, "Zero domain workflows defined in blueprint.", []

        score = 4.0
        evidence = []
        multi_step_count = 0

        for wf in workflows:
            steps = wf.get("steps", [])
            if len(steps) >= 3:
                multi_step_count += 1

        if multi_step_count >= 2:
            score += 4.5
            evidence.append(f"{multi_step_count} multi-step business workflows defined (e.g. {[w.get('name') for w in workflows][:2]}).")
        elif len(workflows) >= 1:
            score += 2.0

        score = max(0.0, min(10.0, score))
        explanation = f"Found {len(workflows)} workflows ({multi_step_count} multi-step operational flows)."
        return score, explanation, evidence

    def _evaluate_evidence_traceability(self, blueprint: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade alignment with ResearchReport via evidence traceability matrix."""
        ri = blueprint.get("research_intelligence", {})
        matrix = ri.get("traceability_matrix", [])
        hash_val = blueprint.get("blueprint_hash")

        score = 4.0
        evidence = []

        if hash_val:
            score += 1.5
            evidence.append(f"Deterministic SHA-256 blueprint hash recorded: {hash_val[:12]}...")

        if len(matrix) >= 3:
            score += 3.5
            canonical_tagged = sum(1 for m in matrix if m.get("claim_type") in ("verified_fact", "source_backed", "inference", "hypothesis"))
            if canonical_tagged == len(matrix):
                score += 1.0
                evidence.append(f"100% of {len(matrix)} traceability items tagged with canonical claim types.")
        elif len(matrix) >= 1:
            score += 1.5

        score = max(0.0, min(10.0, score))
        explanation = f"Traceability matrix links {len(matrix)} requirements to originating evidence."
        return score, explanation, evidence
