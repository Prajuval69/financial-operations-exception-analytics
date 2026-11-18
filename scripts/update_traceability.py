"""Keep rule/KPI and project requirements mapped to real code and verification."""

from pathlib import Path

from app.domain.kpis import CATALOG
from app.domain.rules import RULES

REQUIREMENTS = [
    (
        "FR-01 / 03-04",
        "Deterministic synthetic generation and reference data",
        "app/services/generator.py; app/services/reference.py",
        "tests/test_foundation_data.py; tests/test_rules.py",
        "Verified",
    ),
    (
        "FR-02",
        "Generated data and synthetic CSV ingestion",
        "app/services/ingestion.py",
        "tests/test_foundation_data.py; tests/test_cli.py",
        "Verified",
    ),
    (
        "FR-03 / 05-06",
        "Configurable rules and validation pipeline",
        "app/domain/rules.py; app/services/validation.py; config/policy.json",
        "tests/test_rules.py; tests/test_pipeline_regressions.py",
        "Verified",
    ),
    (
        "FR-04 / 07-09",
        "Exceptions, classification, severity, priority, root causes",
        "app/services/workflow.py; app/domain/priority.py; app/domain/rules.py",
        "tests/test_rules.py; tests/test_analytics_workflow.py",
        "Verified",
    ),
    (
        "FR-05 / 10-12",
        "KPI engine, operational analytics, SLA/TAT",
        "app/domain/kpis.py; app/services/analytics.py",
        "tests/test_analytics_workflow.py; tests/test_scope_and_export.py",
        "Verified",
    ),
    (
        "FR-06 / 13",
        "Actions, dependency cycles, completion and ownership",
        "app/services/workflow.py; app/api/schemas.py",
        "tests/test_analytics_workflow.py; tests/test_api.py",
        "Verified",
    ),
    (
        "FR-07 / 14",
        "Risks, mitigation links and score recalculation",
        "app/services/workflow.py; app/db/models.py",
        "tests/test_analytics_workflow.py; tests/test_scope_and_export.py",
        "Verified",
    ),
    (
        "15",
        "Metric-traceable analytical recommendations",
        "app/services/analytics.py",
        "tests/test_analytics_workflow.py::test_recommendations_trace_observed_metrics",
        "Verified",
    ),
    (
        "FR-11 / 16",
        "FastAPI endpoints, pagination, filters, error responses",
        "app/main.py; app/api/schemas.py",
        "tests/test_api.py; tests/test_scope_and_export.py",
        "Verified; live API checked",
    ),
    (
        "FR-08 / 17",
        "Six-view Streamlit dashboard, exports and forms",
        "dashboard/app.py",
        "tests/test_reports_dashboard.py::test_all_dashboard_views; docs/screenshots",
        "Verified; browser reviewed",
    ),
    (
        "FR-09 / 18",
        "Professional ten-sheet Excel workbook",
        "app/reports/service.py::generate_excel",
        "tests/test_reports_dashboard.py; reports/examples/management.xlsx",
        "Verified",
    ),
    (
        "FR-10 / 19",
        "Offline executive HTML with all sections/charts",
        "app/reports/service.py::generate_executive",
        "tests/test_reports_dashboard.py; tests/test_scope_and_export.py; reports/examples/executive.html",
        "Verified; browser reviewed",
    ),
    (
        "FR-12 / 20",
        "Meaningful automated tests and final quality gates",
        "tests/; .github/workflows/ci.yml",
        "docs/test_results.txt; docs/coverage.json; docs/clean_checkout.json",
        "Local verified; hosted CI not run",
    ),
    (
        "01-02",
        "Project structure, database models and schema initialization",
        "pyproject.toml; app/db/models.py; app/db/session.py",
        "tests/test_foundation_data.py; tests/test_api.py",
        "Verified",
    ),
    (
        "21-22",
        "Structured logging, validation, rollback, error handling",
        "app/core/logging.py; app/api/schemas.py; app/db/session.py; app/main.py",
        "tests/test_api.py; tests/test_cli.py; tests/test_pipeline_regressions.py",
        "Verified",
    ),
    (
        "23",
        "Docker and Compose persistent local stack",
        "Dockerfile; docker-compose.yml; scripts/ensure_demo.py",
        "Static configuration review; Docker executable unavailable",
        "Provided; container runtime unverified",
    ),
    (
        "24",
        "CLI/common-operation and benchmark scripts",
        "app/cli.py; scripts/",
        "tests/test_cli.py; docs/benchmark.json; docs/clean_checkout.json",
        "Verified",
    ),
    (
        "25",
        "Complete setup, methodology and API documentation",
        "README.md; root specifications; docs/METHODOLOGY.md; DATA_DICTIONARY.md",
        "Clean-copy setup verification; final manual cross-check",
        "Verified",
    ),
    (
        "26",
        "Synthetic sample, default demo and example reports",
        "data/demo/; data/reference/; scripts/generate_examples.py; reports/examples/",
        "tests/test_foundation_data.py; tests/test_cli.py; full 50k demo",
        "Verified",
    ),
    (
        "27-28",
        "Requirement traceability and final validation",
        "scripts/update_traceability.py; docs/REQUIREMENTS_TRACEABILITY.md; docs/FINAL_VALIDATION.md",
        "Final definition-of-done review",
        "Verified",
    ),
    (
        "NFR-01",
        "Reproducible, modular, offline, no keys or real data",
        "uv.lock; config/policy.json; domain/services separation",
        "Determinism tests; clean environment; offline HTML browser review",
        "Verified",
    ),
    (
        "NFR-02",
        "Measured performance at 100,000 rows",
        "scripts/benchmark.py",
        "docs/benchmark.json",
        "Measured on Windows; no cross-machine guarantee",
    ),
    (
        "SEC-01",
        "Safe inputs, ORM queries, bounded files and escaped exports",
        "app/api/schemas.py; app/services/ingestion.py; app/reports/service.py",
        "API invalid-input/rollback tests; formula and HTML escaping tests",
        "Verified; trusted-local scope",
    ),
]


def main() -> None:
    lines = [
        "# Requirements Traceability",
        "",
        "Statuses reflect local verification on 2026-10-06. Hosted CI and Docker execution are explicitly distinguished. Original requirement numbers after `/` refer to the pasted 28-item build list.",
        "",
        "| Requirement | Description | Implementation | Test/evidence | Status |",
        "|---|---|---|---|---|",
    ]
    lines += ["| " + " | ".join(row) + " |" for row in REQUIREMENTS]
    lines += [
        "",
        "## Validation controls",
        "",
        "| Rule | Entity / description | Implementation | Test | Status |",
        "|---|---|---|---|---|",
    ]
    for rule in RULES:
        test = (
            "test_each_governance_rule"
            if rule.entity != "transaction"
            else "test_each_transaction_rule"
        )
        lines.append(
            f"| {rule.code} | {rule.entity}: {rule.description} | app/domain/rules.py | tests/test_rules.py::{test}[{rule.code}] | Verified |"
        )
    lines += [
        "",
        "## KPI formulas",
        "",
        "| KPI | Name | Implementation | Test | Status |",
        "|---|---|---|---|---|",
    ]
    for code, (name, _, _) in CATALOG.items():
        test = (
            "test_aging_and_kpi_catalog"
            if code == "KPI032"
            else f"test_every_scalar_kpi_formula[{code}]"
        )
        lines.append(
            f"| {code} | {name} | app/domain/kpis.py | tests/test_analytics_workflow.py::{test} | Verified |"
        )
    Path("docs/REQUIREMENTS_TRACEABILITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
