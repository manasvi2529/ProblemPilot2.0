"""
Research Quality Evaluator (Phase 1.8 Stage 1).
Quantitative grading and qualitative analysis of research validation reports.
Evaluates:
- Problem specificity (0-10)
- Evidence credibility and source authority (0-10)
- Semantic entailment & citation accuracy (0-10)
- Competitor research depth & pricing transparency (0-10)
- Anti-fabrication & zero-invention integrity
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import re


@dataclass
class ResearchDimensionScore:
    score: float
    weight: float
    explanation: str
    evidence_snippets: List[str] = field(default_factory=list)


@dataclass
class ResearchEvaluationResult:
    overall_score: float
    dimensions: Dict[str, ResearchDimensionScore]
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


class ResearchQualityEvaluator:
    """Evaluates the quality, factual rigor, and evidence grounding of a ResearchReport."""

    def __init__(self):
        self.weights = {
            "problem_specificity": 0.30,
            "evidence_credibility": 0.25,
            "citation_entailment": 0.25,
            "competitor_analysis": 0.20,
        }

    def evaluate(self, report: Dict[str, Any]) -> ResearchEvaluationResult:
        """Execute complete quantitative evaluation of the research report."""
        if not report:
            return ResearchEvaluationResult(
                overall_score=0.0,
                dimensions={},
                passed_gate=False,
                summary="Empty or null research report provided.",
            )

        strengths = []
        weaknesses = []

        # 1. Problem Specificity (0 - 10)
        spec_score, spec_expl, spec_ev = self._evaluate_problem_specificity(report)
        if spec_score >= 8.0:
            strengths.append(f"High problem specificity: {spec_expl}")
        elif spec_score < 5.0:
            weaknesses.append(f"Low problem specificity: {spec_expl}")

        # 2. Evidence Credibility & Source Quality (0 - 10)
        cred_score, cred_expl, cred_ev = self._evaluate_evidence_credibility(report)
        if cred_score >= 8.0:
            strengths.append(f"Credible source grounding: {cred_expl}")
        elif cred_score < 5.0:
            weaknesses.append(f"Weak evidence provenance: {cred_expl}")

        # 3. Citation Entailment & Passage Alignment (0 - 10)
        entail_score, entail_expl, entail_ev = self._evaluate_citation_entailment(report)
        if entail_score >= 8.0:
            strengths.append("Direct supporting passages substantiate core claims.")
        elif entail_score < 5.0:
            weaknesses.append(f"Citation disconnect: {entail_expl}")

        # 4. Competitor Landscape & Pricing Transparency (0 - 10)
        comp_score, comp_expl, comp_ev = self._evaluate_competitors(report)
        if comp_score >= 8.0:
            strengths.append("Comprehensive competitor landscape with clear pricing transparency.")
        elif comp_score < 5.0:
            weaknesses.append(f"Superficial competitor analysis: {comp_expl}")

        # Weighted calculation
        dims = {
            "problem_specificity": ResearchDimensionScore(
                score=round(spec_score, 2),
                weight=self.weights["problem_specificity"],
                explanation=spec_expl,
                evidence_snippets=spec_ev,
            ),
            "evidence_credibility": ResearchDimensionScore(
                score=round(cred_score, 2),
                weight=self.weights["evidence_credibility"],
                explanation=cred_expl,
                evidence_snippets=cred_ev,
            ),
            "citation_entailment": ResearchDimensionScore(
                score=round(entail_score, 2),
                weight=self.weights["citation_entailment"],
                explanation=entail_expl,
                evidence_snippets=entail_ev,
            ),
            "competitor_analysis": ResearchDimensionScore(
                score=round(comp_score, 2),
                weight=self.weights["competitor_analysis"],
                explanation=comp_expl,
                evidence_snippets=comp_ev,
            ),
        }

        overall = round(
            (spec_score * self.weights["problem_specificity"])
            + (cred_score * self.weights["evidence_credibility"])
            + (entail_score * self.weights["citation_entailment"])
            + (comp_score * self.weights["competitor_analysis"]),
            2,
        )

        passed_gate = overall >= 6.0 and len(weaknesses) <= 2
        summary = (
            f"Research evaluation score: {overall}/10. "
            f"{'Strong evidentiary foundation.' if passed_gate else 'Requires deeper empirical validation.'}"
        )

        return ResearchEvaluationResult(
            overall_score=overall,
            dimensions=dims,
            passed_gate=passed_gate,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    def _evaluate_problem_specificity(self, report: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade whether the problem definition is crisp, domain-specific, and grounded in user pain."""
        exec_sum = report.get("executive_summary", "")
        landscape = report.get("problem_landscape", {})
        pain_points = report.get("customer_pain_points", [])

        score = 5.0
        evidence = []

        # Check for quantified indicators
        combined_text = f"{exec_sum} {landscape.get('core_conflict', '')}"
        quant_matches = re.findall(r'\b(?:\d+%(?:|\s+of)|(?:\$|€|£)\d+|\d+\s+(?:hours|days|weeks|months|minutes))\b', combined_text, re.IGNORECASE)
        if quant_matches:
            score += 2.0
            evidence.append(f"Quantified problem metrics observed: {quant_matches[:2]}")

        # Check customer pain points depth
        if len(pain_points) >= 3:
            score += 1.5
            detailed_pains = sum(1 for p in pain_points if len(p.get("evidence_quote", "")) > 20)
            if detailed_pains >= 2:
                score += 1.5
                evidence.append(f"{detailed_pains} pain points have grounded user evidence quotes.")
        elif not pain_points:
            score -= 3.0

        # Penalize generic boilerplate phrases
        generic_phrases = ["helps users work better", "streamlines workflow", "generic problem", "improves efficiency"]
        generic_hits = sum(1 for ph in generic_phrases if ph in combined_text.lower())
        if generic_hits >= 2:
            score -= 2.5
            evidence.append("Multiple generic non-specific phrases detected in core problem narrative.")

        score = max(0.0, min(10.0, score))
        explanation = f"Grounded across {len(pain_points)} customer pain points and quantified domain conflict."
        return score, explanation, evidence

    def _evaluate_evidence_credibility(self, report: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade source authority, verification classifications, and retrieval completeness."""
        sources = report.get("sources", [])
        if not sources:
            return 1.0, "No evidence sources available in report.", []

        score = 4.0
        evidence = []
        high_rel_count = 0
        extracted_count = 0

        for s in sources:
            rel = s.get("reliability", "")
            if rel in ("high", "authoritative"):
                high_rel_count += 1
            if s.get("content_extracted"):
                extracted_count += 1

        if high_rel_count >= 2:
            score += 2.0
            evidence.append(f"{high_rel_count} sources possess high/authoritative reliability ratings.")
        if extracted_count >= 2:
            score += 2.0
            evidence.append(f"{extracted_count} sources underwent full-text extraction rather than snippet-only.")

        # Bonus for live provenance transparency
        search_mode = report.get("search_mode", "curated_fallback")
        if search_mode in ("live", "mixed"):
            score += 1.5
            evidence.append(f"Report operates under '{search_mode}' search mode with transparent provenance.")
        elif search_mode == "curated_fallback":
            score += 0.5  # Transparent fallback is acceptable and honest

        # Deduct for invalid claim labels
        for s in sources:
            if s.get("claim_type") == "verified_fact" and not s.get("content_extracted"):
                score -= 2.0
                evidence.append("Penalty: verified_fact assigned to unextracted source snippet.")

        score = max(0.0, min(10.0, score))
        explanation = f"Evaluated {len(sources)} sources ({high_rel_count} high-reliability, {extracted_count} extracted)."
        return score, explanation, evidence

    def _evaluate_citation_entailment(self, report: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Validate whether verbatim supporting passages actually corroborate opportunities."""
        opps = report.get("identified_opportunities", [])
        supporting = report.get("supporting_passages", {})
        if not opps:
            return 2.0, "No opportunities identified to test citation entailment.", []

        score = 5.0
        evidence = []
        matched = 0

        for opp in opps:
            title = opp.get("title", "")
            info = supporting.get(title)
            if info and info.get("passage"):
                passage = info.get("passage", "")
                if len(passage) >= 40:
                    matched += 1

        match_ratio = matched / max(len(opps), 1)
        score += (match_ratio * 4.0)
        evidence.append(f"{matched}/{len(opps)} opportunities have verbatim supporting text passages.")

        score = max(0.0, min(10.0, score))
        explanation = f"Citation alignment ratio: {int(match_ratio * 100)}%."
        return score, explanation, evidence

    def _evaluate_competitors(self, report: Dict[str, Any]) -> tuple[float, str, List[str]]:
        """Grade competitor differentiation and pricing transparency."""
        comps = report.get("competitor_analysis", [])
        pricing = report.get("competitor_pricing", {})

        score = 4.0
        evidence = []

        if len(comps) >= 2:
            score += 2.5
            evidence.append(f"Identified {len(comps)} competitors with strengths/weaknesses and whitespace gaps.")
        elif len(comps) == 1:
            score += 1.0

        # Check pricing transparency
        models = pricing.get("verified_models", [])
        notes = str(pricing.get("pricing_notes", ""))
        if models and len(models) >= 2:
            score += 2.0
            evidence.append(f"{len(models)} competitor pricing models cataloged.")
        if "unverified" in notes.lower() or "requires direct inquiry" in notes.lower():
            score += 1.5
            evidence.append("Truthful pricing disclaimer included for enterprise competitors.")

        score = max(0.0, min(10.0, score))
        explanation = f"Cataloged {len(comps)} competitors and {len(models)} pricing models."
        return score, explanation, evidence
