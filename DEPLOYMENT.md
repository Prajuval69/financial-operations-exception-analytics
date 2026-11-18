# Deployment and Local Runbook

## Preferred local workflow

1. Create virtual environment.
2. Install dependencies.
3. Initialize database.
4. Seed synthetic data.
5. Run validation.
6. Start API.
7. Start dashboard.
8. Generate reports.

## Suggested commands

The exact commands may be finalized by Codex, but should follow this pattern:

```bash
python -m venv .venv
# activate environment
pip install -e ".[dev]"
python -m app.cli init-db
python -m app.cli seed --rows 50000
python -m app.cli validate
uvicorn app.main:app --reload
streamlit run dashboard/app.py
pytest
```

## Docker

Provide Dockerfile and docker-compose.yml where practical.

The Docker setup should expose:
- API
- dashboard

Persist SQLite/data/report directories through volumes where appropriate.

## Troubleshooting

Document:
- database reset
- reseeding
- port changes
- report regeneration
- test failures
- Windows activation instructions

## Final local commands

From the repository root: `uv sync --frozen --extra dev`, then `uv run --frozen --extra dev python -m app.cli demo`. The standard pip path and activation instructions are in README. Separate terminals run `uv run --frozen --extra dev uvicorn app.main:app --host 127.0.0.1 --port 8000` and `uv run --frozen --extra dev streamlit run dashboard/app.py`.

For port conflicts, add `--port 8001` to uvicorn or `--server.port 8502` to Streamlit. The UI does not depend on an API port. Use only trusted local interfaces because authentication is outside scope.

`reset-db --yes` deliberately removes all local database records; choose a different FINOPS_DATABASE_URL to keep the existing demonstration. Seed commands reject nonempty datasets. `report all` regenerates management artifacts; `dictionary` updates the schema dictionary/reference JSON. Revalidation preserves workflow history and does not duplicate findings. Relative configuration paths are resolved from the working directory, so run from the repository root.

CSV input must be synthetic, structurally match the sample, and be ≤250 MiB / one million rows. Invalid values are preserved for detection. Account IDs in the reference CSV must be present/unique. If imports fail, use the locked isolated environment rather than a shared Python installation; Streamlit/FastAPI must have compatible Starlette versions.

Docker Compose defines an idempotent seed job, API and dashboard with persistent data/report volumes and localhost port bindings. `docker compose up --build` is the intended command. Docker is not installed on the implementation host, so container startup has not been executed locally; do not treat static configuration review as a runtime pass. CI is configured for Windows/Linux Python 3.11/3.12, but hosted runs require pushing the repository.

Schema creation is automatic at startup. An additive development upgrade creates/fills transaction_day and its index. Future schema generations require explicit migrations rather than assuming create_all will alter arbitrary tables.
