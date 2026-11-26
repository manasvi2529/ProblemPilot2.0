"""
Phase 1.8 Stage 1 Acceptance Tests: Core Evaluators & Critical Safety Gates.

Tests:
1. Critical Gates evaluated independently.
2. Failed gates force FAILED_GATE regardless of 10.0 numerical dimension scores.
3. Anti-Fabrication Gate catches ungrounded pricing models and fabricated sources.
4. Hypothesis Quarantine Gate verifies unverified features remain in experimental_hypotheses.
5. Evidence Integrity Gate catches semantic disconnect between claims and passages.
6. Security & SSRF Gate evaluates infrastructure controls and secret redaction.
7. ResearchQualityEvaluator scores grounded vs fabricated research reports.
8. BlueprintQualityEvaluator scores domain-specific models vs generic CRUD collapses.
9. AppQualityEvaluator executes sandbox boot, sequential CRUD, input validation, restart persistence, and repair tracing.
10. Exact reproducibility: identical deterministic inputs yield identical scores across repeated runs.
"""
import pytest
import asyncio
import httpx
from pathlib import Path
import unittest.mock as mock

from backend.services.evaluation.critical_gates import (
    CriticalGatesEvaluator,
    GateResult,
    GateEvaluationSummary,
)
from backend.services.evaluation.research_evaluator import ResearchQualityEvaluator
from backend.services.evaluation.blueprint_evaluator import BlueprintQualityEvaluator
from backend.services.evaluation.app_evaluator import AppQualityEvaluator
from backend.services.evaluation.golden_benchmarks import GoldenBenchmarkCase, GoldenBenchmarkDataset
from backend.services.evaluation.benchmark_runner import BenchmarkRunner, BenchmarkCaseRunResult, BenchmarkSuiteSummary


# ==============================================================================
# 1. CRITICAL PASS/FAIL GATES TESTS
# ==============================================================================

class TestCriticalSafetyGates:
    """Tests independent critical gates and the hard rule: Gate Failure forces FAILED_GATE."""

    def test_gate_1_anti_fabrication_detects_unverified_pricing_and_sources(self):
        """Gate 1: Detects fabricated competitor prices and fake sources."""
        # Clean grounded report
        clean_report = {
            "sources": [
                {"url": "https://gov.nist.gov/doc", "title": "NIST Guidelines", "content_extracted": True, "claim_type": "verified_fact"}
            ],
            "competitor_pricing": {
                "verified_models": [{"competitor": "Enterprise Tool", "price": "Custom", "verified": False}],
                "pricing_notes": "Requires direct inquiry / unverified",
            },
        }
        res_clean = CriticalGatesEvaluator.evaluate_anti_fabrication(clean_report)
        assert res_clean.passed is True
        assert len(res_clean.violations) == 0

        # Fabricated report
        fabricated_report = {
            "sources": [
                {"url": "https://example.com/fake-news", "title": "Fake Source", "content_extracted": False, "claim_type": "verified_fact"}
            ],
            "competitor_pricing": {
                "verified_models": [{"competitor": "Nonexistent Corp", "price": "$9,999/mo", "verified": True}],
                "pricing_notes": "Guaranteed price",
            },
        }
        res_fab = CriticalGatesEvaluator.evaluate_anti_fabrication(fabricated_report)
        assert res_fab.passed is False
        assert any("verified price" in v for v in res_fab.violations)
        assert any("Fabricated source URL" in v for v in res_fab.violations)

    def test_gate_2_hypothesis_quarantine_enforcement(self):
        """Gate 2: Enforces that insufficient evidence features must be in experimental_hypotheses."""
        report = {"evidence_sufficiency": "insufficient"}

        # Properly quarantined blueprint
        quarantined_bp = {
            "research_intelligence": {
                "traceability_matrix": [
                    {"requirement": "Automated Anomaly Scoring", "claim_type": "hypothesis"}
                ],
                "experimental_hypotheses": [
                    {"hypothesis": "Automated Anomaly Scoring will reduce audit time by 40%"}
                ],
            }
        }
        res_pass = CriticalGatesEvaluator.evaluate_hypothesis_quarantine(report, quarantined_bp)
        assert res_pass.passed is True

        # Unquarantined blueprint (violates Gate 2)
        leaked_bp = {
            "research_intelligence": {
                "traceability_matrix": [
                    {"requirement": "Unverified Bio-Metric Scanner", "claim_type": "hypothesis"}
                ],
                "experimental_hypotheses": [],
            }
        }
        res_fail = CriticalGatesEvaluator.evaluate_hypothesis_quarantine(report, leaked_bp)
        assert res_fail.passed is False
        assert any("not quarantined" in v for v in res_fail.violations)

    def test_gate_3_evidence_integrity_and_semantic_entailment(self):
        """Gate 3: Enforces that supporting passages logically corroborate claims."""
        # Aligned report
        aligned_report = {
            "identified_opportunities": [{"title": "Automated Invoice Matching Engine"}],
            "supporting_passages": {
                "Automated Invoice Matching Engine": {
                    "passage": "In our enterprise survey, automated invoice matching reduced discrepancy resolution time significantly."
                }
            },
        }
        res_pass = CriticalGatesEvaluator.evaluate_evidence_integrity(aligned_report)
        assert res_pass.passed is True

        # Disconnected report
        disconnected_report = {
            "identified_opportunities": [{"title": "Automated Invoice Matching Engine"}],
            "supporting_passages": {
                "Automated Invoice Matching Engine": {
                    "passage": "Weather reports in Western Europe indicate heavy seasonal precipitation."
                }
            },
        }
        res_fail = CriticalGatesEvaluator.evaluate_evidence_integrity(disconnected_report)
        assert res_fail.passed is False
        assert any("semantic disconnect" in v for v in res_fail.violations)

    def test_gate_4_security_and_ssrf_infrastructure(self):
        """Gate 4: Validates infrastructure controls and unmasked secrets."""
        # Secure context
        clean_ctx = {
            "pinned_ip": "93.184.216.34",
            "trust_env_enabled": False,
            "masked_key": "srp_***1234",
        }
        res_pass = CriticalGatesEvaluator.evaluate_security_and_ssrf(clean_ctx)
        assert res_pass.passed is True

        # Insecure context leaking live secret and private network probe
        leaked_ctx = {
            "api_key": "actual_live_production_secret_key_12345",
            "attempted_private_network_connection": True,
        }
        res_fail = CriticalGatesEvaluator.evaluate_security_and_ssrf(leaked_ctx)
        assert res_fail.passed is False
        assert any("prohibited private IP" in v for v in res_fail.violations)
        assert any("unmasked credential" in v for v in res_fail.violations)

    def test_failed_gate_forces_failed_gate_status_regardless_of_scores(self):
        """Hard Rule: If any gate fails, overall status is FAILED_GATE."""
        report = {
            "sources": [{"url": "https://example.com/fake", "title": "Fake", "content_extracted": False, "claim_type": "verified_fact"}],
            "competitor_pricing": {"verified_models": []},
            "identified_opportunities": [],
        }
        blueprint = {"research_intelligence": {"traceability_matrix": []}}

        summary = CriticalGatesEvaluator.evaluate_all(report, blueprint, security_context={})
        assert summary.overall_passed is False
        assert summary.status == "FAILED_GATE"
        assert len(summary.failure_reasons) > 0


# ==============================================================================
# 2. RESEARCH QUALITY EVALUATOR TESTS
# ==============================================================================

class TestResearchQualityEvaluator:
    """Tests research quality scoring rubrics."""

    def test_grounded_vs_generic_research_scoring(self):
        evaluator = ResearchQualityEvaluator()

        # High-quality grounded report
        grounded_report = {
            "executive_summary": "E-commerce retailers experience 18% margin degradation due to manual cross-border invoice reconciliation taking 25 hours weekly.",
            "problem_landscape": {"core_conflict": "Fragmented multi-currency CSVs cause accounting discrepancies."},
            "customer_pain_points": [
                {"pain_point": "Manual reconciliation toil", "evidence_quote": "Over 78% of finance leads report manual multi-currency matching errors.", "severity": "High"},
                {"pain_point": "Discrepancy audit latency", "evidence_quote": "Month-end close takes 14 business days.", "severity": "High"},
                {"pain_point": "FX conversion variance", "evidence_quote": "Exchange rate slippage accounts for 4% unbudgeted cost.", "severity": "Medium"},
            ],
            "sources": [
                {"url": "https://cdc.gov/study", "title": "CDC Study", "reliability": "high", "content_extracted": True, "claim_type": "source_backed"},
                {"url": "https://nist.gov/report", "title": "NIST Report", "reliability": "high", "content_extracted": True, "claim_type": "verified_fact"},
            ],
            "identified_opportunities": [{"title": "Automated Multi-Currency Invoice Reconciliation"}],
            "supporting_passages": {
                "Automated Multi-Currency Invoice Reconciliation": {
                    "passage": "Automated multi-currency invoice reconciliation eliminates CSV toil and reduces audit close times."
                }
            },
            "competitor_analysis": [
                {"name": "Legacy ERP", "positioning": "Incumbent", "strengths": "Scale", "weaknesses": "Slow", "gap": "Realtime"},
                {"name": "Manual Workarounds", "positioning": "Free", "strengths": "Zero cost", "weaknesses": "High error rate", "gap": "Automation"},
            ],
            "competitor_pricing": {
                "verified_models": [{"competitor": "Legacy ERP", "price": "$1,000/mo", "verified": False}],
                "pricing_notes": "Pricing unverified / requires direct inquiry",
            },
            "search_mode": "live",
        }

        res_grounded = evaluator.evaluate(grounded_report)
        assert res_grounded.overall_score >= 8.0
        assert res_grounded.passed_gate is True

        # Generic report
        generic_report = {
            "executive_summary": "Software helps businesses work better and improves efficiency.",
            "problem_landscape": {"core_conflict": "Generic problem without metrics."},
            "customer_pain_points": [],
            "sources": [],
            "identified_opportunities": [],
            "competitor_analysis": [],
        }

        res_generic = evaluator.evaluate(generic_report)
        assert res_generic.overall_score < 4.5
        assert res_generic.passed_gate is False

    def test_exact_reproducibility_across_identical_runs(self):
        """Exact reproducibility requirement: Identical deterministic inputs yield identical scores."""
        evaluator = ResearchQualityEvaluator()
        sample_report = {
            "executive_summary": "Fintech platform reduces invoice processing time by 10 hours weekly.",
            "problem_landscape": {"core_conflict": "Manual matching is prone to error."},
            "customer_pain_points": [{"pain_point": "Manual toil", "evidence_quote": "Takes too long", "severity": "High"}],
            "sources": [{"url": "https://nist.gov", "reliability": "high", "content_extracted": True}],
            "identified_opportunities": [{"title": "Invoice Tool"}],
            "supporting_passages": {"Invoice Tool": {"passage": "Invoice Tool provides direct automation."}},
            "competitor_analysis": [{"name": "Comp1"}],
        }

        run1 = evaluator.evaluate(sample_report)
        run2 = evaluator.evaluate(sample_report)
        assert run1.overall_score == run2.overall_score
        assert run1.dimensions["problem_specificity"].score == run2.dimensions["problem_specificity"].score
        assert run1.dimensions["evidence_credibility"].score == run2.dimensions["evidence_credibility"].score


# ==============================================================================
# 3. BLUEPRINT QUALITY EVALUATOR TESTS
# ==============================================================================

class TestBlueprintQualityEvaluator:
    """Tests architectural blueprint grading and anti-generic CRUD detection."""

    def test_domain_specific_vs_generic_crud_collapse(self):
        evaluator = BlueprintQualityEvaluator()

        # Domain-rich blueprint
        domain_bp = {
            "title": "Cross-Border Invoice Reconciliation System",
            "domain_entities": [
                {"name": "Invoice", "attributes": [{"name": "id", "type": "string"}, {"name": "amount", "type": "float"}]},
                {"name": "PaymentTransaction", "attributes": [{"name": "id", "type": "string"}, {"name": "invoice_id", "foreign_key": "Invoice.id"}]},
                {"name": "ReconciliationDiscrepancy", "attributes": [{"name": "id", "type": "string"}, {"name": "transaction_id", "foreign_key": "PaymentTransaction.id"}]},
            ],
            "domain_workflows": [
                {"name": "reconcile_invoice_batch", "steps": ["fetch_unmatched", "apply_fx_rate", "match_records", "generate_audit_log"]},
                {"name": "resolve_discrepancy", "steps": ["flag_discrepancy", "notify_auditor", "apply_adjustment"]},
            ],
            "seed_data": {"records": [{"name": "Sample Invoice", "is_synthetic": True}], "is_synthetic": True},
            "blueprint_hash": "sha256_mock_hash_12345",
            "research_intelligence": {
                "traceability_matrix": [
                    {"requirement": "Multi-currency support", "claim_type": "source_backed"},
                    {"requirement": "Automated matching", "claim_type": "verified_fact"},
                    {"requirement": "Audit logging", "claim_type": "source_backed"},
                ]
            },
        }

        res_domain = evaluator.evaluate(domain_bp)
        assert res_domain.overall_score >= 8.0
        assert res_domain.passed_gate is True

        # Generic CRUD collapse
        generic_bp = {
            "title": "Generic Data Manager",
            "domain_entities": [
                {"name": "Item", "attributes": [{"name": "name"}]},
                {"name": "Data", "attributes": [{"name": "value"}]},
                {"name": "Thing", "attributes": [{"name": "description"}]},
            ],
            "domain_workflows": [],
            "seed_data": {},
        }

        res_generic = evaluator.evaluate(generic_bp)
        assert res_generic.overall_score < 4.0
        assert res_generic.passed_gate is False
        assert any("generic" in w.lower() for w in res_generic.weaknesses)


# ==============================================================================
# 4. APPLICATION QUALITY & SANDBOX JOURNEY EVALUATOR TESTS
# ==============================================================================

class TestAppQualityEvaluator:
    """Tests sandbox application execution, CRUD journey testing, and repair tracing."""

    @pytest.mark.asyncio
    async def test_app_evaluation_journey_success(self, tmp_path):
        """Tests successful startup, CRUD calls, input validation, and restart persistence."""
        mock_exec = mock.AsyncMock()
        mock_exec.start_project.return_value = {
            "status": "running",
            "port": 9999,
            "duration": 0.5,
        }
        mock_exec.stop_project.return_value = {"status": "stopped"}

        evaluator = AppQualityEvaluator(execution_engine=mock_exec)

        # Mock HTTP responses for the CRUD journey, input validation, and DOM inspection
        async def mock_send(request):
            import httpx
            url = str(request.url)
            method = request.method

            if "/api/v1/health" in url or (url.endswith(":9999/") and method == "GET"):
                return httpx.Response(200, text="<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width'></head><body>App</body></html>")

            if "/api/v1/records" in url:
                if method == "POST":
                    content = request.read().decode()
                    if "unknown_bad_key" in content:
                        return httpx.Response(422, json={"detail": "Validation error"})
                    return httpx.Response(201, json={"id": "rec_123", "name": "Created Record"})
                elif method == "GET":
                    return httpx.Response(200, json=[{"id": "rec_123", "name": "Created Record"}])
                elif method == "PUT":
                    return httpx.Response(200, json={"id": "rec_123", "name": "Updated Record"})

            return httpx.Response(404, text="Not Found")

        transport = httpx.MockTransport(mock_send)

        with mock.patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=transport)):
            res = await evaluator.evaluate_workspace(
                project_id="test_proj_001",
                user_id="user_test_001",
                workspace_dir=tmp_path,
            )

            assert res.startup_succeeded is True
            assert res.crud_succeeded is True
            assert res.validation_succeeded is True
            assert res.frontend_succeeded is True
            assert res.passed_gate is True
            assert res.overall_score >= 8.0

    @pytest.mark.asyncio
    async def test_app_evaluation_startup_failure_and_repair_trace(self, tmp_path):
        """Tests that startup failure invokes DebuggerService and captures complete repair trace."""
        mock_exec = mock.AsyncMock()
        mock_exec.start_project.return_value = {
            "status": "failed",
            "error": "SyntaxError: invalid syntax in server.py line 42",
            "logs": ['File "server.py", line 42', "SyntaxError: invalid syntax"],
        }
        mock_exec.stop_project.return_value = {"status": "stopped"}

        mock_debugger = mock.AsyncMock()
        mock_debugger.diagnose_error.return_value = {
            "file": "server.py",
            "line": 42,
            "explanation": "Missing colon after if statement",
            "proposed_fix": "if condition:\n    return True",
        }

        evaluator = AppQualityEvaluator(execution_engine=mock_exec, debugger=mock_debugger)

        res = await evaluator.evaluate_workspace(
            project_id="test_proj_fail",
            user_id="user_test_001",
            workspace_dir=tmp_path,
        )

        assert res.startup_succeeded is False
        assert res.passed_gate is False
        assert res.repair_attempted is True
        assert len(res.repair_traces) == 1
        trace = res.repair_traces[0]
        assert trace["diagnostics"]["file"] == "server.py"
        assert trace["diagnostics"]["line"] == 42
        assert "Missing colon" in trace["diagnostics"]["explanation"]

class TestGoldenBenchmarksAndRunner:
    """Tests GoldenBenchmarkDataset integrity and BenchmarkRunner orchestration."""

    def test_golden_dataset_integrity_and_tamper_detection(self):
        dataset = GoldenBenchmarkDataset()
        cases = dataset.list_cases()
        assert len(cases) == 5

        # Check all cases pass integrity verification
        for case in cases:
            assert dataset.verify_integrity(case) is True
            assert len(case.expected_domain_entities) >= 3
            assert len(case.known_competitors) >= 2

        # Verify tamper detection
        c1 = cases[0]
        tampered_case = GoldenBenchmarkCase(
            id=c1.id,
            version=c1.version,
            category=c1.category,
            title="Tampered Title",
            description=c1.description,
            input_prompt=c1.input_prompt,
            expected_domain_entities=c1.expected_domain_entities,
            required_relationships=c1.required_relationships,
            known_competitors=c1.known_competitors,
            unverified_competitor_claims=c1.unverified_competitor_claims,
            required_hypothesis_topics=c1.required_hypothesis_topics,
            ground_truth_evidence=c1.ground_truth_evidence,
            sha256_digest=c1.sha256_digest,  # old digest with changed title
        )
        assert dataset.verify_integrity(tampered_case) is False

    @pytest.mark.asyncio
    async def test_benchmark_runner_single_case_and_report_generation(self, tmp_path):
        dataset = GoldenBenchmarkDataset()
        case = dataset.get_case("case_001_inventory_saas")
        assert case is not None

        runner = BenchmarkRunner()

        grounded_research = {
            "title": "Inventory Saas Research",
            "executive_summary": "18% stockout reduction in regional retail chains through automated reordering rules.",
            "problem_landscape": {
                "core_conflict": "Retail store managers lose $45,000 annually per location due to manual spreadsheet replenishment delays.",
            },
            "metrics": [{"name": "Stockout Rate", "value": "18%"}],
            "customer_pain_points": [
                {"pain_point": "Manual spreadsheet errors", "evidence_quote": "Takes 12 hours weekly", "severity": "High"},
                {"pain_point": "Late supplier POs", "evidence_quote": "Deliveries delayed by 5 days", "severity": "High"},
            ],
            "sources": [
                {
                    "url": "https://katanamrp.com/pricing/",
                    "title": "Katana MRP Pricing",
                    "content_extracted": True,
                    "reliability": "high",
                    "search_mode": "live",
                    "claim_type": "verified_fact",
                    "snippet": "Katana Cloud Inventory pricing tier $129/mo base tier verified on website.",
                }
            ],
            "identified_opportunities": [
                {"title": "Automated Reordering", "target_niche": "Regional Retailers", "why_now": "Supply chain volatility"}
            ],
            "supporting_passages": {
                "Automated Reordering": {
                    "passage": "Automated reordering systems reduce out-of-stock events by 18% based on real-time inventory scans.",
                    "source_url": "https://katanamrp.com/pricing/",
                }
            },
            "competitor_analysis": [
                {"name": "Katana Cloud Inventory", "positioning": "Cloud MRP", "strengths": "Modern UI", "weaknesses": "Complex setup", "gap": "Local dispatch"}
            ],
            "competitor_pricing": {
                "verified_models": [{"competitor": "Katana Cloud Inventory", "price": "$129/mo base tier", "verified": True}],
                "pricing_notes": "Transparent tier verified on official site",
            },
            "search_mode": "live",
            "experimental_hypotheses": [
                "Predictive supplier delivery delays under seasonal demand spikes"
            ],
        }

        rich_blueprint = {
            "title": "Inventory Management Platform",
            "blueprint_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            "domain_entities": [
                {
                    "name": "WarehouseLocation",
                    "fields": [
                        {"name": "id", "type": "str"},
                        {"name": "name", "type": "str"},
                    ],
                    "relationships": ["StockItem"],
                    "constraints": ["UNIQUE(name)"],
                },
                {
                    "name": "StockItem",
                    "fields": [
                        {"name": "id", "type": "str"},
                        {"name": "warehouse_id", "type": "str", "foreign_key": "WarehouseLocation.id"},
                        {"name": "sku", "type": "str"},
                    ],
                    "relationships": ["ReorderRule"],
                    "constraints": ["NOT NULL(sku)"],
                },
                {
                    "name": "ReorderRule",
                    "fields": [
                        {"name": "id", "type": "str"},
                        {"name": "stock_item_id", "type": "str", "foreign_key": "StockItem.id"},
                        {"name": "threshold", "type": "int"},
                    ],
                    "relationships": [],
                    "constraints": ["threshold > 0"],
                },
                {
                    "name": "SupplierPurchaseOrder",
                    "fields": [
                        {"name": "id", "type": "str"},
                        {"name": "stock_item_id", "type": "str", "foreign_key": "StockItem.id"},
                        {"name": "order_date", "type": "str"},
                    ],
                    "relationships": ["StockItem"],
                    "constraints": [],
                },
                {
                    "name": "InventoryAuditLog",
                    "fields": [
                        {"name": "id", "type": "str"},
                        {"name": "stock_item_id", "type": "str", "foreign_key": "StockItem.id"},
                        {"name": "action", "type": "str"},
                    ],
                    "relationships": [],
                    "constraints": [],
                },
            ],
            "workflows": [
                {"name": "Trigger Supplier PO", "steps": ["Check inventory threshold", "Generate PO", "Notify supplier"]},
                {"name": "Stock Reconciliation", "steps": ["Scan warehouse shelf", "Compare ERP count", "Log discrepancy"]},
            ],
            "research_intelligence": {
                "traceability_matrix": [
                    {"requirement": "Multi-location tracking", "source": "cite_1", "claim_type": "verified_fact"},
                    {"requirement": "Automated PO dispatch", "source": "cite_1", "claim_type": "verified_fact"},
                    {"requirement": "Threshold alerting", "source": "cite_1", "claim_type": "source_backed"},
                ]
            },
            "experimental_hypotheses": [
                "Predictive supplier delivery delays under seasonal demand spikes"
            ],
        }

        # Run single case with skip_app_eval=True for static unit testing
        result = await runner.run_single_case(
            case=case,
            research_data=grounded_research,
            blueprint_data=rich_blueprint,
            project_id="test_bench_proj",
            user_id="bench_user",
            workspace_dir=tmp_path,
            skip_app_eval=True,
        )

        assert result.passed_all_gates is True
        assert result.status == "PASSED"
        assert result.overall_score >= 7.0

        # Generate suite report
        suite_report = runner.generate_suite_report(
            suite_id="suite_test_run_001",
            case_results=[result],
        )

        assert suite_report.total_cases == 1
        assert suite_report.passed_cases == 1
        assert suite_report.failed_cases == 0
        assert suite_report.average_score >= 7.0
        assert suite_report.passed_all_critical_gates is True
        assert len(suite_report.sha256_report_digest) == 64


class TestBenchmarkAPIEndpoints:
    """Tests authenticated benchmark endpoints, case listing, and ownership enforcement."""

    def test_unauthenticated_requests_are_rejected(self):
        async def _run():
            from httpx import AsyncClient, ASGITransport
            from backend.main import app

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.get("/api/v1/benchmarks/cases")
                assert res.status_code in (401, 403)

                run_res = await client.post("/api/v1/benchmarks/run", json={})
                assert run_res.status_code in (401, 403)

        asyncio.run(_run())

    def test_authenticated_benchmark_run_lifecycle(self):
        async def _run():
            from httpx import AsyncClient, ASGITransport
            from backend.main import app
            from backend.routers.auth import create_access_token
            from backend.database import init_db, AsyncSessionLocal
            from backend.models.user import User

            await init_db()
            async with AsyncSessionLocal() as db:
                test_user = User(
                    id="bench_user_001",
                    email="eval@test.com",
                    username="evaluator",
                    hashed_password="pw-pre-hashed",
                    operating_mode="autonomous",
                    is_active=True,
                )
                db.add(test_user)
                try:
                    await db.commit()
                except Exception:
                    await db.rollback()

            token = create_access_token({"sub": "bench_user_001", "email": "eval@test.com"})
            headers = {"Authorization": f"Bearer {token}"}

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # 1. List cases
                cases_res = await client.get("/api/v1/benchmarks/cases", headers=headers)
                assert cases_res.status_code == 200
                cases = cases_res.json()
                assert len(cases) == 5

                # 2. Trigger run with single case
                run_res = await client.post(
                    "/api/v1/benchmarks/run",
                    headers=headers,
                    json={"case_ids": ["case_001_inventory_saas"], "skip_app_eval": True},
                )
                assert run_res.status_code == 200
                run_data = run_res.json()
                run_id = run_data["id"]
                assert run_data["status"] == "completed"
                assert run_data["total_cases"] == 1
                assert "sha256_report_digest" in run_data

                # 3. List runs
                list_res = await client.get("/api/v1/benchmarks/runs", headers=headers)
                assert list_res.status_code == 200
                runs = list_res.json()
                assert any(r["id"] == run_id for r in runs)

                # 4. Get run details
                detail_res = await client.get(f"/api/v1/benchmarks/runs/{run_id}", headers=headers)
                assert detail_res.status_code == 200
                details = detail_res.json()
                assert details["id"] == run_id
                assert len(details["case_results"]) == 1
                assert details["case_results"][0]["case_id"] == "case_001_inventory_saas"
                assert "gate_summary" in details["case_results"][0]

        asyncio.run(_run())
