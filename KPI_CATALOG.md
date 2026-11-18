# KPI Catalog

All formulas must be implemented and unit tested.

## Volume

KPI001 Total Transactions
Count of transaction records.

KPI002 Processed Transactions
Count of records with completed processing status.

KPI003 Open Backlog
Count of records not completed.

## Data quality

KPI010 Completeness Rate
Valid mandatory-field observations / total mandatory-field observations.

KPI011 Validity Rate
Records passing validity checks / records evaluated.

KPI012 Duplicate Rate
Duplicate records / total records.

KPI013 Exception Rate
Records with one or more exceptions / total records.

KPI014 Overall Data Quality Score
Weighted portfolio metric combining completeness, validity, consistency, and timeliness. Weights must be configurable and clearly labeled as project methodology, not industry standard.

## Operations

KPI020 Average Processing TAT
Mean processing duration for completed records.

KPI021 Median Processing TAT
Median processing duration.

KPI022 SLA Compliance
Records completed within configured SLA / eligible completed records.

KPI023 Rework Rate
Records requiring rework / processed records.

## Exceptions

KPI030 Open Exceptions
Count of unresolved exceptions.

KPI031 Critical Exceptions
Count of critical open exceptions.

KPI032 Exception Aging
Age of unresolved exceptions grouped into configurable buckets.

KPI033 Average Resolution Time
Average duration between detection and resolution for resolved exceptions.

## Actions

KPI040 Open Actions
Count of incomplete actions.

KPI041 Overdue Actions
Incomplete actions past due date.

KPI042 Action Completion Rate
Completed actions / total actions.

## Risk

KPI050 Open Risks
Count of open risks.

KPI051 High/Critical Risk Count
Count of high or critical risks.

KPI052 Risk Exposure
Configurable aggregate of probability x impact.

## Dashboard principles

Every KPI must display:
- value
- definition
- calculation period/filter context
- source
- timestamp of refresh

## Implementation conventions

All rates are stored as fractions and displayed as percentages. Empty denominators return null/N/A. KPI013 includes resolved exception history; current quality dimensions recompute enabled controls. Validity includes Referential Integrity checks. KPI014 weights default to 0.30/0.30/0.20/0.20 for completeness/validity/consistency/timeliness. Governance failures do not change transaction quality denominators.

TAT/SLA use Completed rows with valid ISO timestamps and finite nonnegative duration; excluded Completed count is exposed in context. SLA includes the exact configured boundary. Rework uses all Completed rows. Cancelled actions are excluded from open/overdue counts but retained in completion-rate denominator. High/critical risk count and risk exposure use open risks only. Exposure is ordinal score, not money.

Definitions, units, values, filter/period/source context, actual refresh timestamp, simulation as-of and policy are emitted together by the KPI service and reused by every output. `docs/METHODOLOGY.md` records boundaries, eligibility, trends, and scoring. All 22 catalog entries have dedicated regression assertions.
