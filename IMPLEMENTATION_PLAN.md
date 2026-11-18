# Implementation Plan

## Milestone 1 — Foundation
- repository
- pyproject
- config
- logging
- database
- models
- schema initialization

## Milestone 2 — Data
- reference data
- deterministic generator
- defect injection
- CSV export/import

## Milestone 3 — Quality
- validation framework
- rule registry
- exception persistence
- summary metrics

## Milestone 4 — Analytics
- KPI service
- trends
- root-cause analysis
- severity/priority
- recommendations

## Milestone 5 — Workflow
- actions
- risks
- ownership
- status transitions
- overdue calculations

## Milestone 6 — API
- FastAPI
- schemas
- endpoints
- pagination/filtering
- OpenAPI

## Milestone 7 — Dashboard
- Streamlit
- filters
- charts
- tables
- recommendations
- exports

## Milestone 8 — Reporting
- Excel
- PDF/HTML
- report artifacts

## Milestone 9 — QA
- unit
- integration
- API
- smoke
- regression

## Milestone 10 — Release
- Docker
- scripts
- documentation
- final validation

## Milestone evidence — 2026-10-06

1. Foundation completed and tested (settings, schema, sessions).
2. Data completed and tested (deterministic source/manifest, references and CSV round-trip).
3. Quality completed and tested (all controls, persistence/idempotence).
4. Analytics completed and tested (all KPI formulas, cohorts, recommendations).
5. Workflow completed and tested (states, dependencies, owners, risks and audit).
6. API completed and tested (routes, filters, pagination, invalid inputs and rollback).
7. Dashboard completed and tested (all six empty/seeded views plus browser review).
8. Reporting completed and tested (ten-sheet workbook and offline executive HTML).
9. QA completed: full suite, lint/format, clean source-copy install/demo and measured 100k workflow.
10. Release artifacts completed: docs, traceability, sample data/reports, screenshots, lockfiles, CI and Docker configuration. Docker runtime/hosted CI remain unexecuted and explicitly documented.

See docs/FINAL_VALIDATION.md for actual results and verification limits.
