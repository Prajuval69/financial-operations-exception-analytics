# Security and Privacy

This is a synthetic portfolio project.

## Rules

- Never use real customer or financial data.
- Never commit API keys, passwords, tokens, or certificates.
- Use local SQLite by default.
- Validate API inputs.
- Avoid SQL string concatenation for user input.
- Do not expose unnecessary filesystem paths.
- Do not expose stack traces in production-style API responses.
- Use safe file handling for uploaded CSV files.
- Restrict generated files to configured output directories.
- Document any development-only configuration.

## Scope

This project is not intended for production financial processing and has not undergone institutional security validation.

## Implemented controls and boundaries

Pydantic rejects unknown fields and invalid enum/range/date values. SQLAlchemy parameterizes queries; no user-controlled SQL interpolation is used. Failed transactions roll back. API unexpected errors return sanitized messages without tracebacks/paths. Reports use configured output directories and generated filenames with atomic replacement; API downloads return content, not paths. HTML is escaped and formula-like text is neutralized in workbook/CSV exports. CSV ingestion is local-only and bounded by size/row limits. No HTTP upload or arbitrary report-path endpoint is exposed.

The API/dashboard bind localhost by default and have no authentication or authorization model. Docker host ports also bind localhost. Anyone with filesystem/API access in this trusted local environment can change the simulated records; audit events are application history, not tamper-proof evidence. Optional config environment variables contain paths/policy only, with no secrets required. Dependency installation/container build may access public package registries; the running workflow and offline report do not require network services. `.venv`, generated databases, logs and real `.env` files are excluded from version control.
