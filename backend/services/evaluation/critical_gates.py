"""
Critical Safety & Integrity Gates for Phase 1.8 Benchmarking.
Evaluates 4 independent critical pass/fail gates:
1. Anti-Fabrication Gate
2. Hypothesis Quarantine Gate
3. Evidence Integrity & Semantic Entailment Gate
4. Infrastructure Security & SSRF Safety Gate

Hard Invariant: A high numerical score can NEVER override a failed gate.
If any critical gate fails, the evaluation overall status is marked 'FAILED_GATE'.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import re


@dataclass
class GateResult:
    """Outcome of an individual critical gate."""
    gate_name: str
    passed: bool
    reason: str
    violations: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GateEvaluationSummary:
    """Aggregate summary of all 4 critical gates."""
    overall_passed: bool
    status: str  # 'PASSED' | 'FAILED_GATE'
    gates: Dict[str, GateResult] = field(default_factory=dict)
    failure_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_passed": self.overall_passed,
            "status": self.status,
            "failure_reasons": self.failure_reasons,
            "gates": {
                k: {
                    "passed": v.passed,
                    "reason": v.reason,
                    "violations": v.violations,
                    "evidence": v.evidence,
                }
                for k, v in self.gates.items()
            },
        }


class CriticalGatesEvaluator:
    """
    Evaluates independent critical gates across research, blueprint, and application artifacts.
    """

    @classmethod
    def evaluate_all(
        cls,
        research_report: Optional[Dict[str, Any]] = None,
        blueprint: Optional[Dict[str, Any]] = None,
        security_context: Optional[Dict[str, Any]] = None,
    ) -> GateEvaluationSummary:
        """Evaluate all 4 critical gates independently and produce aggregated summary."""
        gates = {}
        failure_reasons = []

        # Gate 1: Anti-Fabrication
        g1 = cls.evaluate_anti_fabrication(research_report)
        gates["anti_fabrication"] = g1
        if not g1.passed:
            failure_reasons.append(f"Anti-Fabrication Gate Failed: {g1.reason}")

        # Gate 2: Hypothesis Quarantine
        g2 = cls.evaluate_hypothesis_quarantine(research_report, blueprint)
        gates["hypothesis_quarantine"] = g2
        if not g2.passed:
            failure_reasons.append(f"Hypothesis Quarantine Gate Failed: {g2.reason}")

        # Gate 3: Evidence Integrity & Entailment
        g3 = cls.evaluate_evidence_integrity(research_report)
        gates["evidence_integrity"] = g3
        if not g3.passed:
            failure_reasons.append(f"Evidence Integrity Gate Failed: {g3.reason}")

        # Gate 4: Infrastructure Security & SSRF Safety
        g4 = cls.evaluate_security_and_ssrf(security_context)
        gates["security_and_ssrf"] = g4
        if not g4.passed:
            failure_reasons.append(f"Security & SSRF Gate Failed: {g4.reason}")

        overall_passed = all(g.passed for g in gates.values())
        status = "PASSED" if overall_passed else "FAILED_GATE"

        return GateEvaluationSummary(
            overall_passed=overall_passed,
            status=status,
            gates=gates,
            failure_reasons=failure_reasons,
        )

    @staticmethod
    def evaluate_anti_fabrication(report: Optional[Dict[str, Any]]) -> GateResult:
        """
        Gate 1: Verifies that no invented statistics, pricing, or ungrounded claims
        are masquerading as verified facts.
        """
        if not report:
            return GateResult(
                gate_name="anti_fabrication",
                passed=False,
                reason="Research report is missing or null.",
                violations=["Missing report payload"],
            )

        violations = []
        sources = report.get("sources", [])
        pricing = report.get("competitor_pricing", {})

        # Check pricing verification rules
        verified_models = pricing.get("verified_models", [])
        pricing_notes = str(pricing.get("pricing_notes", "")).lower()

        # If models claim to be verified without supporting citation or inquiry note
        for model in verified_models:
            comp_name = model.get("competitor", "")
            is_verified = model.get("verified", False)
            price = str(model.get("price", ""))

            if is_verified:
                # Must have explicit evidence passage or high-confidence provider
                matching_src = any(
                    comp_name.lower() in (s.get("snippet", "") + s.get("full_text", "")).lower()
                    and any(char.isdigit() for char in price)
                    for s in sources
                )
                if not matching_src and "unverified" not in pricing_notes:
                    violations.append(
                        f"Competitor '{comp_name}' marked as verified price '{price}' without supporting source evidence."
                    )

        # Check for fabricated source indicators
        for s in sources:
            url = str(s.get("url", "")).lower()
            claim_type = s.get("claim_type")
            if "example.com/fake" in url or "hallucinated" in url:
                violations.append(f"Fabricated source URL detected: {url}")
            if claim_type == "verified_fact" and not s.get("content_extracted"):
                violations.append(
                    f"Source '{s.get('title')}' marked verified_fact but content was never deeply extracted."
                )

        passed = len(violations) == 0
        reason = "No ungrounded claims or fabricated sources detected." if passed else "; ".join(violations[:3])
        return GateResult(
            gate_name="anti_fabrication",
            passed=passed,
            reason=reason,
            violations=violations,
            evidence={"checked_models": len(verified_models), "checked_sources": len(sources)},
        )

    @staticmethod
    def evaluate_hypothesis_quarantine(
        report: Optional[Dict[str, Any]],
        blueprint: Optional[Dict[str, Any]],
    ) -> GateResult:
        """
        Gate 2: Verifies that when evidence is moderate or insufficient, unverified features
        are strictly isolated in experimental_hypotheses.
        """
        if not report or not blueprint:
            return GateResult(
                gate_name="hypothesis_quarantine",
                passed=False,
                reason="Report or blueprint payload is missing.",
                violations=["Missing report or blueprint"],
            )

        violations = []
        evidence_sufficiency = str(report.get("evidence_sufficiency", "insufficient")).lower()
        ri = blueprint.get("research_intelligence", {})
        experimental_hypotheses = ri.get("experimental_hypotheses", [])
        traceability_matrix = ri.get("traceability_matrix", [])

        # If evidence is insufficient, requirements mapped to hypotheses must be quarantined
        if evidence_sufficiency == "insufficient":
            for req in traceability_matrix:
                req_claim = str(req.get("claim_type", "")).lower()
                req_name = req.get("requirement", req.get("feature", "Unnamed"))
                if req_claim == "hypothesis":
                    # Must be present in experimental_hypotheses
                    is_quarantined = any(
                        req_name.lower() in str(h.get("hypothesis", "")).lower()
                        or req_name.lower() in str(h.get("feature", "")).lower()
                        for h in experimental_hypotheses
                    )
                    if not is_quarantined:
                        violations.append(
                            f"Requirement '{req_name}' based on hypothesis not quarantined in experimental_hypotheses."
                        )

        # Check for unapproved baseline promotion
        if blueprint.get("promoted_hypotheses_without_approval"):
            violations.append("Experimental hypotheses promoted to baseline architecture without explicit user approval.")

        passed = len(violations) == 0
        reason = "Hypothesis quarantine integrity preserved." if passed else "; ".join(violations[:3])
        return GateResult(
            gate_name="hypothesis_quarantine",
            passed=passed,
            reason=reason,
            violations=violations,
            evidence={"evidence_sufficiency": evidence_sufficiency, "quarantined_count": len(experimental_hypotheses)},
        )

    @staticmethod
    def evaluate_evidence_integrity(report: Optional[Dict[str, Any]]) -> GateResult:
        """
        Gate 3: Evaluates semantic claim-to-passage alignment and citation provenance.
        Verifies that cited supporting passages logically corroborate claims.
        """
        if not report:
            return GateResult(
                gate_name="evidence_integrity",
                passed=False,
                reason="Research report payload is missing.",
                violations=["Missing report"],
            )

        violations = []
        supporting_passages = report.get("supporting_passages", {})
        identified_opportunities = report.get("identified_opportunities", [])

        for opp in identified_opportunities:
            opp_title = opp.get("title", "")
            passage_info = supporting_passages.get(opp_title)
            if not passage_info:
                violations.append(f"Opportunity '{opp_title}' lacks supporting passage mapping.")
                continue

            passage_text = str(passage_info.get("passage", "")).strip()
            if len(passage_text) < 30:
                violations.append(f"Supporting passage for '{opp_title}' is too brief ({len(passage_text)} chars).")

            # Check semantic keyword alignment
            opp_keywords = [w.lower() for w in re.findall(r'\b\w{4,}\b', opp_title)]
            passage_lower = passage_text.lower()
            has_alignment = any(kw in passage_lower for kw in opp_keywords)
            if opp_keywords and not has_alignment:
                violations.append(
                    f"Supporting passage for '{opp_title}' exhibits semantic disconnect (no core subject keywords matched)."
                )

        passed = len(violations) == 0
        reason = "Evidence integrity and passage alignment verified." if passed else "; ".join(violations[:3])
        return GateResult(
            gate_name="evidence_integrity",
            passed=passed,
            reason=reason,
            violations=violations,
            evidence={"opportunities_checked": len(identified_opportunities)},
        )

    @staticmethod
    def evaluate_security_and_ssrf(context: Optional[Dict[str, Any]]) -> GateResult:
        """
        Gate 4: Evaluates benchmark harness infrastructure security, SSRF controls,
        process resource bounds, and secret redaction.
        NOTE: Validates benchmark infrastructure controls only; does NOT certify target application security.
        """
        context = context or {}
        violations = []

        # Check for exposed secrets in context or logs
        for k, v in context.items():
            val_str = str(v)
            if any(term in k.lower() for term in ("secret", "token", "password", "key")) and len(val_str) > 10:
                if not val_str.startswith("mock-") and not val_str.startswith("your-") and "***" not in val_str:
                    violations.append(f"Potential unmasked credential exposed in evaluation context: {k}")

        # Check SSRF guard parameter compliance
        if context.get("attempted_private_network_connection"):
            violations.append("Benchmark harness attempted prohibited private IP network connection.")

        if context.get("trust_env_enabled"):
            violations.append("Client configured with trust_env=True; environment proxies could bypass SSRF guard.")

        passed = len(violations) == 0
        reason = "Benchmark infrastructure security and SSRF safeguards verified." if passed else "; ".join(violations[:3])
        return GateResult(
            gate_name="security_and_ssrf",
            passed=passed,
            reason=reason,
            violations=violations,
            evidence={"disclaimer": "Evaluates benchmark infrastructure security only; does not certify target application."},
        )
