# Exception Catalog

## Categories

1. Completeness
2. Validity
3. Consistency
4. Duplicate
5. Referential Integrity
6. Timeliness
7. Outlier
8. Processing
9. Reconciliation
10. Governance

## Severity

### Critical
Potentially material operational or reporting impact.

### High
Significant issue requiring prompt action.

### Medium
Operational issue requiring planned remediation.

### Low
Minor issue suitable for routine correction.

Severity must be rule-driven and configurable.

## Priority

Priority should consider:
- severity
- age
- transaction amount where applicable
- business impact
- SLA status

Do not imply that the prioritization algorithm is a real financial institution's production policy.

## Root-cause categories

- Missing upstream data
- Invalid source value
- Reference-data mismatch
- Manual entry
- Duplicate submission
- Processing delay
- System integration issue
- Business-rule violation
- Unknown

## Status lifecycle

Detected -> Assigned -> In Progress -> Resolved -> Closed

Allow Reopened from Resolved/Closed where appropriate.
