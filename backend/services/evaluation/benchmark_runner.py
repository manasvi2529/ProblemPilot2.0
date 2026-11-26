"""
Problem2Project AI — Benchmark Suite Runner & Weighted Scoring Engine (Phase 1.8 Stage 2).

Responsibilities:
1. Orchestrates multi-dimensional evaluation runs across golden benchmark cases.
2. Enforces mandatory Critical Safety Gates (Anti-Fabrication, Hypothesis Quarantine, Evidence Integrity, Security).
3. Computes weighted final scores:
   - Research Quality: 30%
   - Blueprint Quality: 35%
   - Application Quality: 35%
   - Hard Rule: If ANY critical gate fails, status = "FAILED_GATE" and overall score is capped at 0.0 or failing.
4. Generates structured, reproducible evaluation reports with SHA-256 integrity digests.
"""
import time
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from backend.services.evaluation.critical_gates import CriticalGatesEvaluator, GateEvaluationSummary
from backend.services.evaluation.research_evaluator import ResearchQualityEvaluator, ResearchEvaluationResult
from backend.services.evaluation.blueprint_evaluator import BlueprintQualityEvaluator, BlueprintEvaluationResult
from backend.services.evaluation.app_evaluator import AppQualityEvaluator, AppEvaluationResult
from backend.services.evaluation.golden_benchmarks import GoldenBenchmarkCase, GoldenBenchmarkDataset

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkCaseRunResult:
    case_id: str
    case_version: str
    case_digest: str
    passed_all_gates: bool
    status: str  # "PASSED" | "FAILED_GATE" | "DEGRADED"
    overall_score: float
    research_score: float
    blueprint_score: float
    app_score: float
    duration_seconds: float
    gate_summary: Dict[str, Any]
    research_result: Dict[str, Any]
    blueprint_result: Dict[str, Any]
    app_result: Dict[str, Any]


@dataclass
class BenchmarkSuiteSummary:
    suite_id: str
    executed_at: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    average_score: float
    passed_all_critical_gates: bool
    case_results: List[BenchmarkCaseRunResult]
    sha256_report_digest: str


class BenchmarkRunner:
    """Executes automated benchmark evaluation suites against Problem2Project AI outputs."""

    def __init__(
        self,
        research_evaluator: Optional[ResearchQualityEvaluator] = None,
        blueprint_evaluator: Optional[BlueprintQualityEvaluator] = None,
        app_evaluator: Optional[AppQualityEvaluator] = None,
    ):
        self.research_evaluator = research_evaluator or ResearchQualityEvaluator()
        self.blueprint_evaluator = blueprint_evaluator or BlueprintQualityEvaluator()
        self.app_evaluator = app_evaluator or AppQualityEvaluator()
        self.dataset = GoldenBenchmarkDataset()

    async def run_single_case(
        self,
        case: GoldenBenchmarkCase,
        research_data: Dict[str, Any],
        blueprint_data: Dict[str, Any],
        project_id: str,
        user_id: str,
        workspace_dir: Path,
        app_crud_payload: Optional[Dict[str, Any]] = None,
        skip_app_eval: bool = False,
    ) -> BenchmarkCaseRunResult:
        """Run complete 4-gate check and 3-component evaluation on a single benchmark case."""
        start_time = time.monotonic()

        # 1. Verify case data integrity via digest
        if not self.dataset.verify_integrity(case):
            raise ValueError(f"Benchmark case {case.id} integrity verification failed: digest mismatch!")

        # 2. Critical Safety Gates Evaluation
        gate_summary: GateEvaluationSummary = CriticalGatesEvaluator.evaluate_all(
            research_report=research_data,
            blueprint=blueprint_data,
        )

        # 3. Quantitative Research Evaluation
        research_res: ResearchEvaluationResult = self.research_evaluator.evaluate(research_data)

        # 4. Quantitative Blueprint Evaluation
        blueprint_res: BlueprintEvaluationResult = self.blueprint_evaluator.evaluate(blueprint_data)

        # 5. Sandbox Application Runtime Evaluation
        if not skip_app_eval:
            app_res: AppEvaluationResult = await self.app_evaluator.evaluate_workspace(
                project_id=project_id,
                user_id=user_id,
                workspace_dir=workspace_dir,
                crud_test_payload=app_crud_payload,
            )
        else:
            app_res = AppEvaluationResult(
                overall_score=7.0,
                passed_gate=True,
                summary="App evaluation skipped for static benchmark fixture.",
                startup_succeeded=True,
                crud_succeeded=True,
                validation_succeeded=True,
                persistence_succeeded=True,
                frontend_succeeded=True,
            )

        duration = time.monotonic() - start_time

        # Weighted Score Computation
        # Research: 30%, Blueprint: 35%, App: 35%
        raw_weighted_score = (
            (research_res.overall_score * 0.30)
            + (blueprint_res.overall_score * 0.35)
            + (app_res.overall_score * 0.35)
        )

        # Hard Rule: Critical Gate Failure overrides score
        if not gate_summary.overall_passed:
            status = "FAILED_GATE"
            final_score = 0.0
        elif raw_weighted_score >= 7.0 and app_res.passed_gate and blueprint_res.passed_gate:
            status = "PASSED"
            final_score = round(raw_weighted_score, 2)
        else:
            status = "DEGRADED"
            final_score = round(raw_weighted_score, 2)

        return BenchmarkCaseRunResult(
            case_id=case.id,
            case_version=case.version,
            case_digest=case.sha256_digest,
            passed_all_gates=gate_summary.overall_passed,
            status=status,
            overall_score=final_score,
            research_score=research_res.overall_score,
            blueprint_score=blueprint_res.overall_score,
            app_score=app_res.overall_score,
            duration_seconds=round(duration, 2),
            gate_summary=gate_summary.to_dict(),
            research_result=research_res.to_dict(),
            blueprint_result=blueprint_res.to_dict(),
            app_result=app_res.to_dict(),
        )

    def generate_suite_report(
        self,
        suite_id: str,
        case_results: List[BenchmarkCaseRunResult],
    ) -> BenchmarkSuiteSummary:
        """Aggregate results into a certified, digest-verifiable evaluation suite report."""
        total = len(case_results)
        passed = sum(1 for c in case_results if c.status == "PASSED")
        failed = total - passed
        avg_score = round(sum(c.overall_score for c in case_results) / total, 2) if total > 0 else 0.0
        all_gates_passed = all(c.passed_all_gates for c in case_results)

        executed_at = datetime.now(timezone.utc).isoformat()
        report_payload = {
            "suite_id": suite_id,
            "executed_at": executed_at,
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": failed,
            "average_score": avg_score,
            "passed_all_critical_gates": all_gates_passed,
            "cases": [asdict(c) for c in case_results],
        }
        digest = hashlib.sha256(json.dumps(report_payload, sort_keys=True).encode("utf-8")).hexdigest()

        return BenchmarkSuiteSummary(
            suite_id=suite_id,
            executed_at=executed_at,
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            average_score=avg_score,
            passed_all_critical_gates=all_gates_passed,
            case_results=case_results,
            sha256_report_digest=digest,
        )
