# Data Dictionary

Generated from SQLAlchemy schema by `python -m app.cli dictionary`.

| Entity | Field | Type | Nullable | Description | Allowed values | Example | Source | Validation |
|---|---|---|---|---|---|---|---|---|
| accounts | account_id | VARCHAR(60) | False | Account id. | See entity schema/reference data | 1 | Synthetic generator / synthetic CSV | Schema/service invariants |
| accounts | account_type | VARCHAR(40) | False | Account type. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| accounts | business_unit_id | VARCHAR(60) | False | Business unit id. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| accounts | country | VARCHAR(10) | False | Country. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| accounts | currency | VARCHAR(10) | False | Currency. | USD, EUR, GBP, INR, JPY, SGD (raw transactions may fail) | USD | Synthetic generator / synthetic CSV | Schema/service invariants |
| accounts | status | VARCHAR(30) | False | Status. | Entity lifecycle/reference values; raw transaction values are validated | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| accounts | created_at | VARCHAR(40) | False | Created at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Synthetic generator / synthetic CSV | Schema/service invariants |
| audit_events | id | INTEGER | False | Internal surrogate identity; source transaction IDs may be defective or repeated. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| audit_events | entity | VARCHAR(30) | False | Entity. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| audit_events | entity_id | INTEGER | False | Entity id. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| audit_events | occurred_at | VARCHAR(40) | False | Occurred at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
| audit_events | changes | JSON | False | Audit field differences with before and after values. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| dataset_meta | id | INTEGER | False | Internal surrogate identity; source transaction IDs may be defective or repeated. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| dataset_meta | as_of | VARCHAR(40) | False | Simulation timestamp used consistently for SLA, aging, and overdue calculations. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| dataset_meta | seed | INTEGER | True | Seed. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| dataset_meta | ingested_at | VARCHAR(40) | False | Actual UTC ingestion timestamp, distinct from simulation time. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
| dataset_meta | source | VARCHAR(200) | False | Source. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| reference_values | id | INTEGER | False | Internal surrogate identity; source transaction IDs may be defective or repeated. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| reference_values | kind | VARCHAR(40) | False | Kind. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| reference_values | code | VARCHAR(60) | False | Code. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| reference_values | label | VARCHAR(120) | False | Label. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| transactions | id | INTEGER | False | Internal surrogate identity; source transaction IDs may be defective or repeated. | See entity schema/reference data | 1 | Synthetic generator / synthetic CSV | Schema/service invariants |
| transactions | transaction_id | VARCHAR(80) | True | Transaction id. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | DQ001, DQ030 |
| transactions | account_id | VARCHAR(60) | True | Account id. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | DQ002, DQ050 |
| transactions | business_unit_id | VARCHAR(60) | True | Business unit id. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | DQ006, DQ016 |
| transactions | source_system_id | VARCHAR(60) | True | Source system id. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | DQ052 |
| transactions | transaction_date | VARCHAR(40) | True | Source transaction timestamp; raw text preserves malformed dates for detection. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Synthetic generator / synthetic CSV | DQ003, DQ017 |
| transactions | transaction_day | VARCHAR(10) | True | Derived valid transaction date in UTC for reliable SQL date filters; null for malformed or missing source dates. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| transactions | processing_date | VARCHAR(40) | True | Source completion timestamp; missing for unprocessed rows. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Synthetic generator / synthetic CSV | DQ018, DQ019, DQ020, DQ040, DQ041 |
| transactions | transaction_type | VARCHAR(40) | True | Transaction type. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | DQ013 |
| transactions | amount | VARCHAR(80) | True | Raw amount text; validation controls numeric conversion. No cross-currency monetary totals. | See entity schema/reference data | 125.50 | Synthetic generator / synthetic CSV | DQ004, DQ010, DQ011, DQ060 |
| transactions | currency | VARCHAR(20) | True | Currency. | USD, EUR, GBP, INR, JPY, SGD (raw transactions may fail) | USD | Synthetic generator / synthetic CSV | DQ005, DQ012 |
| transactions | status | VARCHAR(40) | True | Status. | Entity lifecycle/reference values; raw transaction values are validated | Synthetic value | Synthetic generator / synthetic CSV | DQ014 |
| transactions | priority | VARCHAR(20) | True | Priority. | P1, P2, P3, P4 | P2 | Synthetic generator / synthetic CSV | DQ015 |
| transactions | team_id | VARCHAR(60) | True | Team id. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | DQ051 |
| transactions | owner | VARCHAR(100) | True | Owner. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| transactions | reference_code | VARCHAR(100) | True | Reference code. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| transactions | rework | BOOLEAN | False | Synthetic flag that processing required rework. | true/false | false | Synthetic generator / synthetic CSV | Schema/service invariants |
| transactions | created_at | VARCHAR(40) | False | Created at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Synthetic generator / synthetic CSV | Schema/service invariants |
| transactions | updated_at | VARCHAR(40) | False | Updated at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Synthetic generator / synthetic CSV | Schema/service invariants |
| transactions | raw | JSON | False | Original source values, retained for investigation before type coercion. | See entity schema/reference data | Synthetic value | Synthetic generator / synthetic CSV | Schema/service invariants |
| validation_runs | id | INTEGER | False | Internal surrogate identity; source transaction IDs may be defective or repeated. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| validation_runs | as_of | VARCHAR(40) | False | Simulation timestamp used consistently for SLA, aging, and overdue calculations. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| validation_runs | created_at | VARCHAR(40) | False | Created at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
| validation_runs | summary | JSON | False | Validation run counts by rule at the recorded simulation time. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| validation_runs | policy | JSON | False | Validated rule thresholds and weights captured at validation time. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | exception_id | INTEGER | False | Exception id. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| exceptions | record_id | INTEGER | True | Internal transaction row identity; lineage remains unambiguous for duplicate source IDs. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | source_entity | VARCHAR(30) | False | Source entity. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | source_record_id | VARCHAR(80) | False | Primary identity in source_entity, independent of defective external transaction ID. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | transaction_id | VARCHAR(80) | True | Transaction id. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | rule_code | VARCHAR(20) | False | Rule code. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | category | VARCHAR(40) | False | Category. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | description | TEXT | False | Description. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | suggested_action | TEXT | False | Suggested action. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | severity | VARCHAR(20) | False | Severity. | Low, Medium, High, Critical | High | Local application service | Schema/service invariants |
| exceptions | priority | VARCHAR(10) | False | Priority. | P1, P2, P3, P4 | P2 | Local application service | Schema/service invariants |
| exceptions | status | VARCHAR(30) | False | Status. | Entity lifecycle/reference values; raw transaction values are validated | Synthetic value | Local application service | Schema/service invariants |
| exceptions | root_cause | VARCHAR(60) | False | Root cause. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | business_impact | TEXT | False | Business impact. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| exceptions | owner | VARCHAR(100) | True | Owner. | See entity schema/reference data | Synthetic value | Local application service | DQ023 |
| exceptions | detected_at | VARCHAR(40) | False | Detection timestamp; demo includes explicitly simulated historical detections. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
| exceptions | due_date | VARCHAR(40) | False | Due date. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
| exceptions | resolved_at | VARCHAR(40) | True | Resolved at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | DQ021 |
| exceptions | resolution_notes | TEXT | True | Resolution notes. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| processing_events | event_id | INTEGER | False | Event id. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| processing_events | record_id | INTEGER | False | Internal transaction row identity; lineage remains unambiguous for duplicate source IDs. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| processing_events | transaction_id | VARCHAR(80) | True | Transaction id. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| processing_events | stage | VARCHAR(40) | False | Stage. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| processing_events | event_timestamp | VARCHAR(40) | False | Event timestamp. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| processing_events | team_id | VARCHAR(60) | True | Team id. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| processing_events | status | VARCHAR(40) | False | Status. | Entity lifecycle/reference values; raw transaction values are validated | Synthetic value | Local application service | Schema/service invariants |
| processing_events | duration_minutes | FLOAT | False | Duration minutes. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| processing_events | exception_flag | BOOLEAN | False | Exception flag. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| actions | action_id | INTEGER | False | Action id. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| actions | exception_id | INTEGER | True | Exception id. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| actions | title | VARCHAR(200) | False | Title. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| actions | description | TEXT | False | Description. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| actions | owner | VARCHAR(100) | False | Owner. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| actions | priority | VARCHAR(10) | False | Priority. | P1, P2, P3, P4 | P2 | Local application service | Schema/service invariants |
| actions | due_date | VARCHAR(40) | False | Due date. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
| actions | status | VARCHAR(30) | False | Status. | Entity lifecycle/reference values; raw transaction values are validated | Synthetic value | Local application service | Schema/service invariants |
| actions | dependency | INTEGER | True | Dependency. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| actions | created_at | VARCHAR(40) | False | Created at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
| actions | completed_at | VARCHAR(40) | True | Completed at. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | DQ022 |
| risks | risk_id | INTEGER | False | Risk id. | See entity schema/reference data | 1 | Local application service | Schema/service invariants |
| risks | related_exception_id | INTEGER | True | Related exception id. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| risks | action_id | INTEGER | True | Action id. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| risks | title | VARCHAR(200) | False | Title. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| risks | description | TEXT | False | Description. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| risks | probability | INTEGER | False | Probability. | Integer 1–5 | 3 | Local application service | Schema/service invariants |
| risks | impact | INTEGER | False | Impact. | Integer 1–5 | 4 | Local application service | Schema/service invariants |
| risks | risk_score | INTEGER | False | Ordinal probability × impact score; not monetary or institution-approved risk exposure. | Integer 1–25 | Synthetic value | Local application service | Schema/service invariants |
| risks | owner | VARCHAR(100) | False | Owner. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| risks | status | VARCHAR(30) | False | Status. | Entity lifecycle/reference values; raw transaction values are validated | Synthetic value | Local application service | Schema/service invariants |
| risks | mitigation | TEXT | False | Mitigation. | See entity schema/reference data | Synthetic value | Local application service | Schema/service invariants |
| risks | due_date | VARCHAR(40) | False | Due date. | ISO datetime for timestamp fields; see schema for other values | 2026-09-30T18:00:00 | Local application service | Schema/service invariants |
