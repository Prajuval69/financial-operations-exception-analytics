# API Specification

Use FastAPI and expose OpenAPI documentation.

## Health

GET /health

Returns service status.

## Transactions

GET /api/v1/transactions
Filters:
- business_unit
- team
- status
- source_system
- date_from
- date_to
- page
- page_size

GET /api/v1/transactions/{transaction_id}

## Validation

POST /api/v1/validation/run

Runs validation against available data.

GET /api/v1/validation/summary

Returns rule-level counts and quality metrics.

## Exceptions

GET /api/v1/exceptions

Filters:
- status
- severity
- priority
- category
- owner
- root_cause

GET /api/v1/exceptions/{exception_id}

PATCH /api/v1/exceptions/{exception_id}

Supports assignment, status, priority, resolution notes.

## Actions

GET /api/v1/actions

POST /api/v1/actions

PATCH /api/v1/actions/{action_id}

## Risks

GET /api/v1/risks

POST /api/v1/risks

PATCH /api/v1/risks/{risk_id}

## KPIs

GET /api/v1/kpis/summary
GET /api/v1/kpis/trends
GET /api/v1/kpis/exceptions
GET /api/v1/kpis/teams

## Reports

POST /api/v1/reports/excel
POST /api/v1/reports/executive

The API should return useful HTTP status codes, validation errors, and structured JSON responses.

## Implemented contract

Start with `uvicorn app.main:app --host 127.0.0.1 --port 8000`. `/docs` is the interactive OpenAPI reference and `/openapi.json` is machine-readable.

List routes return `{items, total, page, page_size}`, default 50 rows, maximum 500. Page ≥1. ISO date filters are inclusive normalized UTC days; date_from after date_to returns 422. KPIs and reports accept transaction business_unit/team/status/source_system/date_from/date_to filters. Unknown IDs return 404, ambiguous duplicated external transaction IDs return 409, invalid values/nulls return 422, invalid state transitions/dependencies return 409. Unexpected failures return sanitized 500 responses.

Exception PATCH accepts owner, status, priority and resolution_notes. Lifecycle is Detected → Assigned → In Progress → Resolved → Closed, with Reopened from Resolved/Closed. High/critical findings require an owner. Resolution notes are required and resolution time is populated automatically.

Action POST requires title, owner and ISO due_date; optional exception_id, dependency, description and priority. Action statuses: Open, In Progress, Blocked, Completed, Cancelled. Completion time is automatic. Cycles and incomplete dependencies block completion. Risk POST requires title, owner, due_date, probability and impact (strict integers 1–5); optional related_exception_id, action_id, description and mitigation. Risk status is Open/Mitigating/Closed; score is always recomputed.

Validation body optionally includes ISO as_of, which updates simulation time. Reports return downloadable Excel/HTML content (Content-Disposition attachment) with server-generated names. Additional endpoints: GET `/api/v1/references`, GET `/api/v1/audit`.

Example JSON: action creation `{"title":"Review source mapping","owner":"Control Desk","due_date":"2026-10-07T18:00:00","priority":"P2"}`. Exception assignment `{"owner":"Control Desk","status":"Assigned"}`. Use OpenAPI for complete request/response shapes and query options.
