# Codex Master Build Prompt

You are the lead software engineer, data engineer, analytics engineer, QA engineer, technical writer, and release engineer for this repository.

Build the entire **Financial Operations Data Quality & Exception Analytics Platform** from this repository's markdown specifications.

## Operating rules

1. Read all `.md` files before implementing.
2. Treat `SPECIFICATION.md` as the product contract.
3. Treat `ARCHITECTURE.md` as the architectural baseline.
4. Implement incrementally in phases.
5. Do not stop at scaffolding.
6. Generate all required source code, configuration, tests, seed data, reports, and documentation.
7. Run tests and fix failures.
8. Do not fabricate test results.
9. Do not use real customer, bank, fund, or proprietary data.
10. Do not require internet access at runtime.
11. Do not require Power BI Desktop.
12. Keep the application runnable on Windows and Linux where practical.
13. Use environment variables only for optional configuration; no secrets are needed.
14. Prefer deterministic synthetic data using a documented random seed.
15. Keep business logic separate from UI code.
16. Validate all externally supplied API inputs.
17. Use type hints and clear module boundaries.
18. Add logging around ingestion, validation, processing, and report generation.
19. Make failures actionable with useful error messages.
20. Update documentation when implementation decisions differ from the specification.

## Required execution sequence

### Phase 1 — Repository inspection
Read:
- README.md
- SPECIFICATION.md
- ARCHITECTURE.md
- DATA_MODEL.md
- VALIDATION_RULES.md
- KPI_CATALOG.md
- EXCEPTION_CATALOG.md
- API_SPEC.md
- DASHBOARD_SPEC.md
- EXCEL_REPORT_SPEC.md
- EXECUTIVE_REPORT_SPEC.md
- TEST_PLAN.md
- SECURITY.md
- DEPLOYMENT.md
- IMPLEMENTATION_PLAN.md
- DEFINITION_OF_DONE.md

### Phase 2 — Foundation
Create project structure, dependency management, configuration, database layer, logging, migrations/schema initialization, and CLI entry points.

### Phase 3 — Synthetic data
Implement deterministic generation of realistic operational records, reference data, injected data-quality defects, and expected validation outcomes.

### Phase 4 — Data quality engine
Implement all validation rules and exception generation.

### Phase 5 — Reconciliation/exception analytics
Implement exception classification, severity, priority, aging, root-cause analytics, and action tracking.

### Phase 6 — KPI engine
Implement every KPI in `KPI_CATALOG.md` with unit tests and documented formulas.

### Phase 7 — API
Implement all endpoints in `API_SPEC.md`.

### Phase 8 — Dashboard
Implement all dashboard requirements in `DASHBOARD_SPEC.md`. The dashboard must work with seeded local data.

### Phase 9 — Excel and executive report
Implement the required workbook and PDF/HTML executive report.

### Phase 10 — QA
Run unit, integration, API, data-quality, and smoke tests. Fix failures rather than weakening tests.

### Phase 11 — Documentation
Ensure setup, architecture, data dictionary, API usage, dashboard usage, testing, assumptions, and limitations are complete.

### Phase 12 — Release validation
Perform a clean local build/test from a fresh environment if possible. Produce a final validation report.

## Final response/report

At completion, provide:
- What was built
- How to run it
- Test command and actual result
- Generated artifacts
- Known limitations
- Any deviations from the specification

Do not say "complete" unless the definition of done has been checked.
