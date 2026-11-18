# Measurement methodology

Every record is synthetic; thresholds/scales are project assumptions.

## Data grain and controls

An internal `transactions.id` identifies one ingested row even when the source ID is missing/duplicated. Original values remain in `raw`. Amounts/dates retain source text; `transaction_day` normalizes valid ISO dates to UTC for SQL filtering.

All 24 specified rules plus DQ017/DQ018 malformed transaction/processing dates and DQ019 missing completion timestamp are implemented. Missing mandatory fields trigger completeness errors without duplicate numeric/reference findings for the same missing value. Type/status/priority/team/source must have controlled values even when absent.

DQ030 flags nonblank duplicates beyond the first. DQ020 honors chronology tolerance; DQ040 independently flags negative TAT. DQ041 flags completed durations or pending age over SLA. DQ060 uses nominal record amount in its own currency without FX normalization; it is illustrative rather than a monetary materiality policy.

DQ021/DQ022/DQ023 scan persisted exceptions/actions. Revalidation preserves resolutions, avoids duplicate findings and recalculates severity/priority. Resolved exceptions can retain unresolved source defects as reviewed history. Corrected source rules auto-resolve open findings. Disabling controls leaves their historical findings unchanged. Validation snapshots capture counts and policy.

## Denominators

Completeness = present observations / (six mandatory fields × rows), always evaluating all six fields. Validity = rows passing enabled validity/reference rules / rows. Consistency/timeliness = rows passing enabled transaction consistency/timeliness rules / rows. Governance findings do not silently change a transaction quality denominator.

Default quality = 0.30 completeness + 0.30 validity + 0.20 consistency + 0.20 timeliness. Weights are nonnegative and sum to one; disabled controls change the evaluated set. Duplicate/outlier findings remain independently visible. Exception rate counts distinct internal transaction rows with persisted history, including resolved items. Empty denominators are null/N/A.

Completed status defines processed count; every other/unknown status is backlog. Eligible TAT/SLA also requires valid dates and nonnegative finite duration. Mean/median use eligible completions; SLA includes the exact threshold. Excluded Completed rows are disclosed. Rework uses all Completed rows as denominator.

Temporal views group by valid UTC origination day. Exception trends count rows with exception history. Backlog trends show current backlog cohorts, not historical stocks. Process events simulate Intake/Control/Settlement at 15%/35%/50% of nonnegative source duration. Team/day rates recompute numerator/denominator. Missing-date rows remain in totals without invented temporal placement.

## Priority, aging and workflow

Severity is rule-driven and overrideable. Priority starts at Critical=4, High=3, Medium=2, Low=1. Age ≥7 days, SLA breach, amount over threshold and material reporting impact each add a point. Escalation is capped at two and total at four; 4/3/2/1 map to P1/P2/P3/P4. Revalidation also recalculates manually edited priorities.

Aging uses fractional days at simulation as-of, floored at zero. Default buckets: ≤2, (2,7], (7,14], (14,30], >30 days. Resolution averages valid nonnegative detection-to-resolution durations for Resolved/Closed records.

Open actions exclude Completed/Cancelled. Overdue means due timestamp < as-of. Completion rate divides Completed by all actions, including Cancelled. Dependency cycles are rejected; dependencies must finish before dependent completion. Edits produce before/after audit events.

Risk probability/impact use 1–5 ordinal scales. Score = probability × impact. High/critical is ≥12 by default. Exposure sums open-risk scores; it is not monetary exposure. Closed risks are excluded.

## Recommendations, time and scope

Triggers: duplicates ≥0.5%, SLA <95%, completeness <99.9%, any open critical exception, overdue action, high-scoring open risk, or open finding >30 days. Recommendation thresholds are explicit in `derive_recommendations`; operational thresholds/weights live in policy JSON. Suggestions include metric code/value, as-of and investigation. Rule-derived root-cause labels are not proven causal findings.

Naive ISO timestamps mean UTC; aware inputs normalize. Seed 42 and fixed as-of reproduce records and defects. Ingestion/audit/report creation use actual UTC time; report names/refresh timestamps vary. Byte-identical reports are not promised.

Transaction filters scope linked exceptions/actions/risks/events. Unlinked global workflow items appear only in the full portfolio. Reports use the same calculation services. Excel samples cap at 1,000 transactions; exception/action/risk sheets include all scoped rows. Executive detail tables cap at 20 with truncation labels; all 22 KPIs remain present.
