# Final validation — 2026-10-06

The local application workflow and definition of done were reviewed against the repository specification. All requested application components are implemented. Docker execution and hosted CI are explicitly unverified; neither is represented as a passing runtime test.

## Executed quality gates

| Check | Actual result | Evidence |
|---|---|---|
| Full pytest suite | 89 passed; one upstream Starlette/AnyIO deprecation warning | test_results.txt |
| Coverage | 95% overall rounded; KPI formulas, priority and analytics calculations fully exercised | coverage.json |
| Ruff lint / formatting | Passed; source formatting checked | clean_checkout.json |
| Fresh source copy and isolated install | Lockfile installation, lint, formatting, all 89 tests and 1,000-row demo passed | clean_checkout.json |
| Default local demonstration | 50,000 transactions, 5,000 accounts, 6,000 injected rows, 6,478 persisted findings, 80 actions, 30 risks | reports/examples/kpi_snapshot.json; generated database |
| Revalidation | Zero new/duplicate findings on unchanged data; lifecycle preserved | CLI run + idempotency regressions |
| API live HTTP | Health OK; 50,000-row summary agrees with dashboard | localhost:8000; API tests |
| Streamlit application | All six views passed with empty/seeded databases; live Executive/Data Quality/Exceptions views inspected | AppTest regressions; screenshots |
| Excel workbook | Ten sheets, frozen/filterable headers, numeric percentages/dates, chart and scoped row counts verified | Report tests; reports/examples/management.xlsx |
| Executive HTML | All sections/KPIs, embedded offline charts, escaped content and metric-traceable recommendations verified; opened from local file | Report tests; reports/examples/executive.html |
| Git hygiene | Virtual environment, generated DBs/logs and .env excluded; examples/source/docs included | .gitignore and git check-ignore |

The full suite command was `python -m pytest --cov=app --cov=dashboard --cov-report=term-missing --cov-report=json:docs/coverage.json -q --tb=short`. Last recorded coverage run completed in 38.60 seconds on the implementation environment. The final isolated clean-copy run repeats the full suite after final configuration changes. The dependency warning comes from Starlette's use of a deprecated AnyIO portal alias, not a test failure; it is retained rather than suppressed.

## Measured scale check

`python scripts/benchmark.py --rows 100000` used seed 42, 5,000 accounts and the fixed simulation timestamp in an isolated temporary SQLite database:

| Stage | Measured seconds |
|---|---:|
| Generation and ingestion | 10.145 |
| Validation | 2.962 |
| Analytics | 7.398 |

The 100k dataset produced 12,963 findings and its total count was asserted. These are Windows 11 / Python 3.12.4 measurements, not performance guarantees for other hardware. The benchmark separates these service stages and does not include browser paint or report generation. Exact environment/results: benchmark.json.

## Review outcomes and decisions

- All 24 specified controls and three added timestamp controls are tested. Every one of the 22 KPI catalog entries has a numerical/bucket regression assertion.
- Defective source IDs/types are preserved under internal identities rather than rejected before validation.
- The fixed simulation clock separates deterministic business metrics from real ingestion/audit/report timestamps.
- UI and API reuse application services; the local UI can run without the API server.
- HTML was selected from the allowed PDF/HTML output options. It opens offline and can be printed; direct PDF generation is not claimed.
- Reference dimensions use a controlled-value table rather than separate ORM classes for each small catalog.
- Temporal views are explicitly origination cohorts. Source quality, resolved exception history, invalid-duration exclusions and ordinal risk exposure are labeled consistently.
- Git was initialized on main. No commit, remote push or external publication was performed.

## Remaining verification limits

Docker is not installed on this host, so the Dockerfile/Compose setup has been reviewed but not built or launched. Windows Python 3.12 is the tested host; Linux/Python 3.11 execution awaits the configured GitHub Actions matrix. The API/dashboard have no authentication and are intended for trusted localhost use. This synthetic portfolio simulation is not an institutional control system, contains no live feeds/FX conversion, and provides rule-based analytical suggestions rather than financial advice.

All definition-of-done items are accounted for in the root checklist and REQUIREMENTS_TRACEABILITY.md; no requirement has a blank status.
