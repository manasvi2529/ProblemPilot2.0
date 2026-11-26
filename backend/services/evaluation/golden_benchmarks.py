"""
Problem2Project AI — Versioned Golden Benchmark Dataset (Phase 1.8 Stage 2).

Provides 5 diverse, deterministic golden evaluation benchmark cases:
1. inventory_management_saas: Vertical SaaS with multi-tier pricing, inventory/supplier models, and strict SLA constraints.
2. telehealth_compliance_portal: Healthcare SaaS requiring HIPAA compliance hypotheses, encrypted records, and audit logs.
3. developer_devtools_cli: Developer productivity tool with CLI/API endpoints, telemetry, and rate limiting.
4. local_artisan_marketplace: Multi-vendor e-commerce with commission splits, product catalog, and delivery tracking.
5. ai_prompt_testing_hub: AI evaluation workspace with token budgeting, prompt versioning, and test runs.

Each benchmark defines:
- Canonical inputs (problem discovery statement, target audience, technical constraints)
- Expected domain entities and required relationships
- Anti-fabrication ground truth (known competitor models and citation checks)
- SHA-256 integrity digest for exact version reproducibility
"""
import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass(frozen=True)
class GoldenBenchmarkCase:
    id: str
    version: str
    category: str
    title: str
    description: str
    input_prompt: str
    expected_domain_entities: List[str]
    required_relationships: List[str]
    known_competitors: List[str]
    unverified_competitor_claims: List[str]
    required_hypothesis_topics: List[str]
    ground_truth_evidence: List[Dict[str, str]]
    sha256_digest: str


BENCHMARK_CASES_DATA = [
    {
        "id": "case_001_inventory_saas",
        "version": "1.0.0",
        "category": "vertical_b2b_saas",
        "title": "Automated Multi-Location Inventory Management",
        "description": "Inventory reconciliation, stock forecasting, and automated supplier reordering for small retail chains.",
        "input_prompt": "Build a multi-location inventory and automated purchase order management platform for regional retail stores suffering from 18% annual stockout losses.",
        "expected_domain_entities": ["WarehouseLocation", "StockItem", "SupplierPurchaseOrder", "ReorderRule", "InventoryAuditLog"],
        "required_relationships": ["WarehouseLocation -> StockItem", "StockItem -> ReorderRule", "SupplierPurchaseOrder -> StockItem"],
        "known_competitors": ["Katana Cloud Inventory", "Cin7", "inFlow Inventory"],
        "unverified_competitor_claims": ["Katana 100% discount for enterprise", "Secret free tier at Cin7 with no item limits"],
        "required_hypothesis_topics": ["Predictive supplier delivery delays under seasonal demand spikes"],
        "ground_truth_evidence": [
            {
                "citation_id": "cite_inv_01",
                "source_url": "https://www.retaildive.com/news/inventory-distortion-cost-retailers/589000/",
                "claim": "Retail inventory distortion accounts for significant stockout and overstock losses across regional mid-market retail.",
                "supporting_passage": "According to IHL Group research cited by Retail Dive, out-of-stocks and overstocks cost retailers over 1.1 trillion globally each year.",
            },
            {
                "citation_id": "cite_inv_02",
                "source_url": "https://katanamrp.com/pricing/",
                "claim": "Katana Cloud Inventory offers structured standard and professional pricing tiers for manufacturers and distributors.",
                "supporting_passage": "Katana pricing starts with transparent monthly tiers based on order volume and connected warehouse locations.",
            }
        ]
    },
    {
        "id": "case_002_telehealth_portal",
        "version": "1.0.0",
        "category": "healthcare_compliance",
        "title": "HIPAA-Compliant Patient Telehealth & Intake Portal",
        "description": "Secure patient intake, encrypted clinical notes, consent management, and HIPAA-compliant video session scheduling.",
        "input_prompt": "Create a compliant telehealth intake and appointment management application for independent behavioral health therapists.",
        "expected_domain_entities": ["TherapistProfile", "PatientRecord", "IntakeConsent", "ClinicalSession", "AccessAuditTrail"],
        "required_relationships": ["TherapistProfile -> ClinicalSession", "PatientRecord -> IntakeConsent", "PatientRecord -> ClinicalSession"],
        "known_competitors": ["SimplePractice", "TheraPlatform", "Doxy.me"],
        "unverified_competitor_claims": ["SimplePractice unlimited free tier with zero BAA requirements"],
        "required_hypothesis_topics": ["State-by-state cross-border licensure reciprocity for teletherapy"],
        "ground_truth_evidence": [
            {
                "citation_id": "cite_hlth_01",
                "source_url": "https://www.hhs.gov/hipaa/for-professionals/special-topics/telehealth/index.html",
                "claim": "Telehealth platforms handling PHI require Business Associate Agreements and end-to-end access audit controls.",
                "supporting_passage": "Under HIPAA regulations, covered healthcare providers must obtain satisfactory assurances from business associates to protect protected health information.",
            }
        ]
    },
    {
        "id": "case_003_devtools_cli",
        "version": "1.0.0",
        "category": "developer_tools",
        "title": "Cloud Cost Optimization & Anomaly Detection CLI",
        "description": "Continuous AWS and GCP resource scanning, idle instance termination recommendations, and cost spike alerting.",
        "input_prompt": "Develop an engineering-focused cloud cost anomaly alert engine that analyzes infrastructure metrics and flags abandoned staging clusters.",
        "expected_domain_entities": ["CloudAccountCredential", "ResourceUsageMetric", "CostAnomalyEvent", "OptimizationPolicy", "SlackAlertChannel"],
        "required_relationships": ["CloudAccountCredential -> ResourceUsageMetric", "ResourceUsageMetric -> CostAnomalyEvent"],
        "known_competitors": ["Vantage", "CloudZero", "Infracost"],
        "unverified_competitor_claims": ["CloudZero proprietary zero-cost free cloud monitoring"],
        "required_hypothesis_topics": ["Automatic preemptible instance replacement during continuous integration pipeline execution"],
        "ground_truth_evidence": [
            {
                "citation_id": "cite_dev_01",
                "source_url": "https://www.infracost.io/docs/",
                "claim": "Infracost estimates cloud costs directly in pull requests before provisioning cloud infrastructure.",
                "supporting_passage": "Infracost sits inside the developer CI/CD workflow to detect cloud cost increases before terraform apply.",
            }
        ]
    },
    {
        "id": "case_004_artisan_marketplace",
        "version": "1.0.0",
        "category": "marketplace_ecommerce",
        "title": "Hyperlocal Artisan Bakery & Specialty Foods Hub",
        "description": "Order batching, perishable goods lead-time tracking, localized courier routing, and seller payouts.",
        "input_prompt": "Build an online marketplace for neighborhood specialty bakeries to take pre-orders for limited-batch sourdough and pastries.",
        "expected_domain_entities": ["BakerStorefront", "ArtisanProduct", "ProductionBatch", "CustomerPreOrder", "PayoutRecord"],
        "required_relationships": ["BakerStorefront -> ArtisanProduct", "ArtisanProduct -> ProductionBatch", "ProductionBatch -> CustomerPreOrder"],
        "known_competitors": ["Hotplate", "Castiron", "BakeDiary"],
        "unverified_competitor_claims": ["Hotplate 0% transaction fee and free nationwide refrigerated shipping"],
        "required_hypothesis_topics": ["Customer willingness to pick up warm deliveries within strict 30-minute baking windows"],
        "ground_truth_evidence": [
            {
                "citation_id": "cite_mkt_01",
                "source_url": "https://www.hotplate.com/about",
                "claim": "Hotplate provides pre-order drops and batch notifications for micro-bakers and pop-up chefs.",
                "supporting_passage": "Hotplate helps culinary creators launch scheduled drops and manage limited inventory via automated SMS alerts.",
            }
        ]
    },
    {
        "id": "case_005_prompt_testing_hub",
        "version": "1.0.0",
        "category": "ai_tooling",
        "title": "LLM Prompt Evaluation & Regression Testing Hub",
        "description": "Systematic evaluation of prompt versions against fixed test datasets, latency scoring, and output regression diffs.",
        "input_prompt": "Create an LLM prompt evaluation workbench allowing teams to run assertion-based regression tests on system prompts across model versions.",
        "expected_domain_entities": ["PromptTemplate", "PromptVersion", "TestCaseDataset", "EvaluationRunRecord", "AssertionResult"],
        "required_relationships": ["PromptTemplate -> PromptVersion", "PromptVersion -> EvaluationRunRecord", "TestCaseDataset -> EvaluationRunRecord"],
        "known_competitors": ["Promptfoo", "Braintrust", "LangSmith"],
        "unverified_competitor_claims": ["LangSmith unlimited free private traces without billing account setup"],
        "required_hypothesis_topics": ["Synthetic judge accuracy correlations against senior domain human annotators"],
        "ground_truth_evidence": [
            {
                "citation_id": "cite_llm_01",
                "source_url": "https://www.promptfoo.dev/docs/getting-started/",
                "claim": "Promptfoo is an open-source CLI and library for evaluating LLM prompts and application output quality.",
                "supporting_passage": "Promptfoo allows developers to define test suites in YAML with deterministic assertions and LLM-assisted grading.",
            }
        ]
    }
]


def _compute_benchmark_digest(data: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 digest of benchmark case data."""
    raw = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class GoldenBenchmarkDataset:
    """Repository of immutable, version-pinned evaluation benchmarks."""

    def __init__(self):
        self._cases: Dict[str, GoldenBenchmarkCase] = {}
        for raw in BENCHMARK_CASES_DATA:
            digest = _compute_benchmark_digest({k: v for k, v in raw.items() if k != "sha256_digest"})
            case = GoldenBenchmarkCase(
                id=raw["id"],
                version=raw["version"],
                category=raw["category"],
                title=raw["title"],
                description=raw["description"],
                input_prompt=raw["input_prompt"],
                expected_domain_entities=list(raw["expected_domain_entities"]),
                required_relationships=list(raw["required_relationships"]),
                known_competitors=list(raw["known_competitors"]),
                unverified_competitor_claims=list(raw["unverified_competitor_claims"]),
                required_hypothesis_topics=list(raw["required_hypothesis_topics"]),
                ground_truth_evidence=list(raw["ground_truth_evidence"]),
                sha256_digest=digest,
            )
            self._cases[case.id] = case

    def list_cases(self) -> List[GoldenBenchmarkCase]:
        return list(self._cases.values())

    def get_case(self, case_id: str) -> Optional[GoldenBenchmarkCase]:
        return self._cases.get(case_id)

    def verify_integrity(self, case: GoldenBenchmarkCase) -> bool:
        """Verify that the case has not been mutated or tampered with."""
        d = asdict(case)
        d.pop("sha256_digest", None)
        expected = _compute_benchmark_digest(d)
        return case.sha256_digest == expected
