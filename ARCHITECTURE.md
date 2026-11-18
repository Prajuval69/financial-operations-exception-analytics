# Architecture

## High-level architecture

```text
                    Synthetic Data Generator
                              |
                              v
                    CSV / SQLite Ingestion
                              |
                              v
                     Validation Engine
                              |
               +--------------+--------------+
               |                             |
               v                             v
        Valid Operational Data       Exception Records
               |                             |
               +--------------+--------------+
                              |
                              v
                         KPI Engine
                              |
                +-------------+-------------+
                |                           |
                v                           v
          FastAPI Services            Reporting Engine
                |                           |
                v                    +------+------+
          Streamlit UI               |             |
                              Excel Workbook   PDF/HTML
```

## Layering

### Presentation
Streamlit dashboard and report templates.

### API
FastAPI routes, request/response schemas.

### Application
Use cases such as:
- ingest data
- run validation
- calculate KPIs
- create actions
- resolve exceptions
- generate reports

### Domain
Business rules, validation rules, severity/priority calculations, KPI formulas.

### Data
SQLAlchemy models, SQLite database, repositories, seed scripts.

### Infrastructure
Configuration, logging, file I/O, report generation.

## Design principles

- Separation of concerns.
- Single responsibility.
- Explicit validation.
- Deterministic processing.
- Testable business rules.
- No business logic hidden in dashboard code.

## Suggested repository

```text
financial-ops-analytics/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── domain/
│   ├── services/
│   ├── reports/
│   └── main.py
├── dashboard/
├── data/
│   ├── raw/
│   ├── processed/
│   └── reference/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
├── docs/
├── reports/
├── config/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

Codex may refine the structure while preserving separation of concerns.

## Implemented architecture

`app/domain` contains pure vectorized control/KPI logic. `app/services` owns ingestion, validation, analytics and audited state transitions. `app/main.py` exposes those services through FastAPI. Streamlit calls the same services directly against SQLite, so it does not require an API server to be running. This is a deliberate local-first refinement of the suggested API-to-UI diagram.

Reference entities use a controlled-value table, while accounts have a dedicated table. Transactions use a surrogate identity and retain raw source values so defective external identifiers/types can be investigated without losing lineage. SQLite foreign keys protect application relationships. Read/write sessions commit atomically and roll back on failures. WAL and a busy timeout support the local API/dashboard pair.

Schema initialization creates all tables and performs the documented additive UTC transaction-day upgrade for earlier development databases. This release is a single schema generation, not a general enterprise migration framework. Future schema changes require explicit migrations.

HTML reporting was selected from the allowed PDF/HTML choices. Plotly runtime is embedded for offline charts. Excel uses openpyxl. Runtime dependencies are locked in `uv.lock`, with exported pip requirements and container/CI configuration. See `docs/METHODOLOGY.md` for all calculation choices.
