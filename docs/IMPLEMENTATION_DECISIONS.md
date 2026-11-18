# Implementation decisions

The requested Python/FastAPI/SQLAlchemy/Pydantic/Pandas/NumPy/Streamlit/Plotly/openpyxl stack is used. Executive HTML was selected from the permitted PDF/HTML choices, removing a PDF-toolchain requirement while keeping charts and a printable artifact offline.

Source transaction ID is nullable/nonunique, with an internal surrogate row ID. Amounts/dates remain source text. This supports defective-data validation and unambiguous exception linkage. The original source record remains in JSON. A derived normalized UTC day fixes date filtering without concealing invalid dates.

Small controlled catalogs share one reference table; accounts remain their own table. Audit events, validation snapshots and dataset metadata make the local workflow inspectable. Schema creation includes one additive development upgrade. General enterprise migrations, authentication, tenancy and tamper-proof audit storage are beyond this release's documented scope.

The Streamlit dashboard calls application services directly rather than making HTTP calls to a required backend. Both surfaces share business logic/database. This makes the local application more reproducible and preserves the API as a separately demonstrable interface.

Validation preserves resolved history and automatically resolves open findings when source controls pass. Priority recalculates on validation; configured policy, latest source checks, persisted history and manual reviews are explicitly distinguished. Three date controls were added to prevent silently unusable completion metrics.

All temporal calculations normalize ISO timestamps to UTC, with a fixed simulation as-of separate from actual refresh/audit clocks. Null denominators show N/A. Money is not summed across currencies; ordinal risk scores are not currency exposure. Origination-day charts do not claim historical queue reconstruction. Full definitions and boundaries are in METHODOLOGY.md.

Tests are grouped by concern under tests instead of unused unit/integration/API subdirectories. Meaningful fixtures and end-to-end paths replace skeleton scaffolding. Runtime versions are locked; standard pip requirements and a CI matrix support the same code on other hosts. Docker is provided but not locally run because its executable is unavailable.
