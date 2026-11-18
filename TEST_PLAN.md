# Test Plan

## Unit tests

Test:
- every validation rule
- every KPI formula
- severity calculation
- priority calculation
- aging buckets
- recommendation rules
- date calculations
- data generator determinism

## Integration tests

Test:
- database initialization
- seed process
- validation pipeline
- exception persistence
- KPI calculations against seeded database
- report generation

## API tests

Test:
- health endpoint
- transaction filters
- exception retrieval/update
- action creation/update
- KPI endpoints
- invalid input handling
- pagination

## Dashboard smoke tests

At minimum verify that:
- app imports
- data loads
- KPI queries execute
- expected dashboard functions can be imported/executed
- missing/empty data does not crash the app

## Data-quality tests

Assert that intentionally injected defects are detected by expected rules.

## Regression tests

Keep representative fixtures and expected KPI outputs.

## Quality gate

All automated tests must pass before release.

## Executable evidence

Run `uv run --frozen --extra dev pytest --cov=app --cov=dashboard --cov-report=term-missing`. Unit/integration/API tests are organized by concern under tests, rather than empty directory scaffolding. Every registry rule and catalog KPI has a parameterized regression assertion and a coverage-completeness check.

Tests include all expected synthetic defects, nonfinite/negative numeric values, ISO dates and UTC filtering, policy overrides, idempotent validation, automatic source-correction resolution, persisted governance controls, audited lifecycle transitions, dependency cycles, risk recalculation, pagination, invalid inputs/rollback, report sheets/formats/content, formula/HTML escaping, CLI round-trip and all six Streamlit AppTest views with empty and seeded data.

`scripts/clean_checkout_check.py` installs into a temporary source copy/fresh environment, runs lint/format/full tests and executes a fresh demo. `scripts/benchmark.py` measures an isolated 100k-row pipeline. Live browser/HTTP checks and screenshots complement automated tests. Actual commands/results are in docs/FINAL_VALIDATION.md; raw test/coverage/clean-copy/benchmark evidence is retained under docs. Docker and hosted CI execution are explicitly reported separately from local checks.
