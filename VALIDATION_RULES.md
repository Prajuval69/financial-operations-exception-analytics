# Data Validation Rules

Each rule must have a unique code, deterministic behavior, severity, and test coverage.

## Completeness

DQ001 — transaction_id must not be null.

DQ002 — account_id must not be null.

DQ003 — transaction_date must not be null.

DQ004 — amount must not be null.

DQ005 — currency must not be null.

DQ006 — business_unit_id must not be null.

## Validity

DQ010 — amount must be numeric.

DQ011 — amount must be greater than or equal to zero.

DQ012 — currency must exist in reference data.

DQ013 — transaction_type must exist in reference data.

DQ014 — status must exist in reference data.

DQ015 — priority must exist in reference data.

DQ016 — business_unit_id must exist in reference data.

## Consistency

DQ020 — processing_date must not precede transaction_date beyond an allowed tolerance.

DQ021 — resolved exception must have resolved_at.

DQ022 — completed action must have completed_at.

DQ023 — high/critical exceptions must have an owner.

## Uniqueness

DQ030 — transaction_id must be unique within the source dataset.

## Timeliness

DQ040 — processing turnaround must not be negative.

DQ041 — records older than configured operational SLA should be flagged.

## Referential integrity

DQ050 — account_id must exist in account reference data.

DQ051 — team_id must exist in team reference data.

DQ052 — source_system_id must exist in source reference data.

## Outlier detection

DQ060 — configurable high-value threshold should flag unusual transaction amounts.

The outlier threshold must be configurable and clearly documented; do not present it as an industry-standard threshold.

## Rule output

Every failed rule should produce an exception containing:
- rule code
- category
- severity
- description
- source record ID
- detected timestamp
- suggested action

## Implemented additions and interpretation

- DQ017: nonblank transaction_date must be a valid ISO date/time (Validity, High).
- DQ018: nonblank processing_date must be a valid ISO date/time (Validity, High).
- DQ019: Completed records require processing_date (Consistency, High).

These additions prevent malformed/missing dates from silently distorting analytics. DQ010 accepts finite numbers only. DQ030 flags repeated nonblank IDs beyond the first, using internal row identity. DQ041 uses completed turnaround or pending age against the simulation clock. Missing mandatory fields receive completeness findings; independent numeric/reference checks avoid repeating the same missing-value failure. Type/status/priority/team/source must be controlled values even when absent.

Policies are configured in `config/policy.json`. Governance rules evaluate persisted exception/action entities and preserve their lineage. Every catalog rule is covered by a positive/negative test; synthetic injected defects have a deterministic expected-rule manifest. See `docs/METHODOLOGY.md` for rerun/history behavior.
