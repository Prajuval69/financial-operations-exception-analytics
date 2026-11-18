# Requirements Traceability

Statuses reflect local verification on 2026-10-06. Hosted CI and Docker execution are explicitly distinguished. Original requirement numbers after `/` refer to the pasted 28-item build list.

| Requirement | Description | Implementation | Test/evidence | Status |
|---|---|---|---|---|
| FR-01 / 03-04 | Deterministic synthetic generation and reference data | app/services/generator.py; app/services/reference.py | tests/test_foundation_data.py; tests/test_rules.py | Verified |
| FR-02 | Generated data and synthetic CSV ingestion | app/services/ingestion.py | tests/test_foundation_data.py; tests/test_cli.py | Verified |
| FR-03 / 05-06 | Configurable rules and validation pipeline | app/domain/rules.py; app/services/validation.py; config/policy.json | tests/test_rules.py; tests/test_pipeline_regressions.py | Verified |
| FR-04 / 07-09 | Exceptions, classification, severity, priority, root causes | app/services/workflow.py; app/domain/priority.py; app/domain/rules.py | tests/test_rules.py; tests/test_analytics_workflow.py | Verified |
| FR-05 / 10-12 | KPI engine, operational analytics, SLA/TAT | app/domain/kpis.py; app/services/analytics.py | tests/test_analytics_workflow.py; tests/test_scope_and_export.py | Verified |
| FR-06 / 13 | Actions, dependency cycles, completion and ownership | app/services/workflow.py; app/api/schemas.py | tests/test_analytics_workflow.py; tests/test_api.py | Verified |
| FR-07 / 14 | Risks, mitigation links and score recalculation | app/services/workflow.py; app/db/models.py | tests/test_analytics_workflow.py; tests/test_scope_and_export.py | Verified |
| 15 | Metric-traceable analytical recommendations | app/services/analytics.py | tests/test_analytics_workflow.py::test_recommendations_trace_observed_metrics | Verified |
| FR-11 / 16 | FastAPI endpoints, pagination, filters, error responses | app/main.py; app/api/schemas.py | tests/test_api.py; tests/test_scope_and_export.py | Verified; live API checked |
| FR-08 / 17 | Six-view Streamlit dashboard, exports and forms | dashboard/app.py | tests/test_reports_dashboard.py::test_all_dashboard_views; docs/screenshots | Verified; browser reviewed |
| FR-09 / 18 | Professional ten-sheet Excel workbook | app/reports/service.py::generate_excel | tests/test_reports_dashboard.py; reports/examples/management.xlsx | Verified |
| FR-10 / 19 | Offline executive HTML with all sections/charts | app/reports/service.py::generate_executive | tests/test_reports_dashboard.py; tests/test_scope_and_export.py; reports/examples/executive.html | Verified; browser reviewed |
| FR-12 / 20 | Meaningful automated tests and final quality gates | tests/; .github/workflows/ci.yml | docs/test_results.txt; docs/coverage.json; docs/clean_checkout.json | Local verified; hosted CI not run |
| 01-02 | Project structure, database models and schema initialization | pyproject.toml; app/db/models.py; app/db/session.py | tests/test_foundation_data.py; tests/test_api.py | Verified |
| 21-22 | Structured logging, validation, rollback, error handling | app/core/logging.py; app/api/schemas.py; app/db/session.py; app/main.py | tests/test_api.py; tests/test_cli.py; tests/test_pipeline_regressions.py | Verified |
| 23 | Docker and Compose persistent local stack | Dockerfile; docker-compose.yml; scripts/ensure_demo.py | Static configuration review; Docker executable unavailable | Provided; container runtime unverified |
| 24 | CLI/common-operation and benchmark scripts | app/cli.py; scripts/ | tests/test_cli.py; docs/benchmark.json; docs/clean_checkout.json | Verified |
| 25 | Complete setup, methodology and API documentation | README.md; root specifications; docs/METHODOLOGY.md; DATA_DICTIONARY.md | Clean-copy setup verification; final manual cross-check | Verified |
| 26 | Synthetic sample, default demo and example reports | data/demo/; data/reference/; scripts/generate_examples.py; reports/examples/ | tests/test_foundation_data.py; tests/test_cli.py; full 50k demo | Verified |
| 27-28 | Requirement traceability and final validation | scripts/update_traceability.py; docs/REQUIREMENTS_TRACEABILITY.md; docs/FINAL_VALIDATION.md | Final definition-of-done review | Verified |
| NFR-01 | Reproducible, modular, offline, no keys or real data | uv.lock; config/policy.json; domain/services separation | Determinism tests; clean environment; offline HTML browser review | Verified |
| NFR-02 | Measured performance at 100,000 rows | scripts/benchmark.py | docs/benchmark.json | Measured on Windows; no cross-machine guarantee |
| SEC-01 | Safe inputs, ORM queries, bounded files and escaped exports | app/api/schemas.py; app/services/ingestion.py; app/reports/service.py | API invalid-input/rollback tests; formula and HTML escaping tests | Verified; trusted-local scope |

## Validation controls

| Rule | Entity / description | Implementation | Test | Status |
|---|---|---|---|---|
| DQ001 | transaction: Transaction ID is required | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ001] | Verified |
| DQ002 | transaction: Account ID is required | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ002] | Verified |
| DQ003 | transaction: Transaction date is required | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ003] | Verified |
| DQ004 | transaction: Amount is required | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ004] | Verified |
| DQ005 | transaction: Currency is required | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ005] | Verified |
| DQ006 | transaction: Business unit is required | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ006] | Verified |
| DQ010 | transaction: Amount must be finite numeric | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ010] | Verified |
| DQ011 | transaction: Amount cannot be negative | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ011] | Verified |
| DQ012 | transaction: Currency must be a reference value | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ012] | Verified |
| DQ013 | transaction: Transaction type must be a reference value | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ013] | Verified |
| DQ014 | transaction: Status must be a reference value | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ014] | Verified |
| DQ015 | transaction: Priority must be a reference value | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ015] | Verified |
| DQ016 | transaction: Business unit must exist | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ016] | Verified |
| DQ017 | transaction: Transaction date must be ISO datetime | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ017] | Verified |
| DQ018 | transaction: Processing date must be ISO datetime | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ018] | Verified |
| DQ019 | transaction: Completed records need a processing date | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ019] | Verified |
| DQ020 | transaction: Processing date precedes transaction date beyond tolerance | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ020] | Verified |
| DQ021 | exception: Resolved/closed exceptions require a valid resolution time | app/domain/rules.py | tests/test_rules.py::test_each_governance_rule[DQ021] | Verified |
| DQ022 | action: Completed actions require a valid completion time | app/domain/rules.py | tests/test_rules.py::test_each_governance_rule[DQ022] | Verified |
| DQ023 | exception: High/critical exceptions require an owner | app/domain/rules.py | tests/test_rules.py::test_each_governance_rule[DQ023] | Verified |
| DQ030 | transaction: Transaction ID is duplicated within dataset | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ030] | Verified |
| DQ040 | transaction: Processing turnaround is negative | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ040] | Verified |
| DQ041 | transaction: Processing or open age exceeds configured SLA | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ041] | Verified |
| DQ050 | transaction: Account reference does not exist | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ050] | Verified |
| DQ051 | transaction: Team reference does not exist | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ051] | Verified |
| DQ052 | transaction: Source system reference does not exist | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ052] | Verified |
| DQ060 | transaction: Amount exceeds project high-value threshold | app/domain/rules.py | tests/test_rules.py::test_each_transaction_rule[DQ060] | Verified |

## KPI formulas

| KPI | Name | Implementation | Test | Status |
|---|---|---|---|---|
| KPI001 | Total Transactions | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI001] | Verified |
| KPI002 | Processed Transactions | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI002] | Verified |
| KPI003 | Open Backlog | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI003] | Verified |
| KPI010 | Completeness Rate | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI010] | Verified |
| KPI011 | Validity Rate | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI011] | Verified |
| KPI012 | Duplicate Rate | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI012] | Verified |
| KPI013 | Exception Rate | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI013] | Verified |
| KPI014 | Overall Data Quality Score | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI014] | Verified |
| KPI020 | Average Processing TAT | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI020] | Verified |
| KPI021 | Median Processing TAT | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI021] | Verified |
| KPI022 | SLA Compliance | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI022] | Verified |
| KPI023 | Rework Rate | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI023] | Verified |
| KPI030 | Open Exceptions | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI030] | Verified |
| KPI031 | Critical Exceptions | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI031] | Verified |
| KPI032 | Exception Aging | app/domain/kpis.py | tests/test_analytics_workflow.py::test_aging_and_kpi_catalog | Verified |
| KPI033 | Average Resolution Time | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI033] | Verified |
| KPI040 | Open Actions | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI040] | Verified |
| KPI041 | Overdue Actions | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI041] | Verified |
| KPI042 | Action Completion Rate | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI042] | Verified |
| KPI050 | Open Risks | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI050] | Verified |
| KPI051 | High/Critical Risk Count | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI051] | Verified |
| KPI052 | Risk Exposure | app/domain/kpis.py | tests/test_analytics_workflow.py::test_every_scalar_kpi_formula[KPI052] | Verified |
