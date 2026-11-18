# Dashboard Specification

Use Streamlit and Plotly unless a better local-only alternative is justified.

## Page 1 — Executive Overview

Cards:
- Total Transactions
- Exception Rate
- Data Quality Score
- SLA Compliance
- Open Exceptions
- Critical Exceptions
- Overdue Actions

Charts:
- transaction volume trend
- exception trend
- SLA trend
- exceptions by category

## Page 2 — Data Quality

Show:
- completeness
- validity
- consistency
- duplicates
- timeliness
- rule-level failures

Charts:
- quality score by source
- quality score by business unit
- rule failure Pareto
- trend

## Page 3 — Operational Performance

Show:
- average TAT
- median TAT
- SLA compliance
- backlog
- rework

Charts:
- TAT distribution
- SLA by team
- backlog trend
- process-stage performance

## Page 4 — Exceptions

Filters:
- status
- severity
- priority
- category
- team
- owner
- date

Show:
- exception table
- aging buckets
- root causes
- top recurring rules

## Page 5 — Actions & Risks

Show:
- open actions
- overdue actions
- action completion rate
- open risks
- high/critical risks
- upcoming deadlines

## Page 6 — Recommendations

Automatically derive rule-based recommendations from metrics.

Examples:
- High duplicate rate -> investigate source duplication.
- Low SLA compliance -> inspect processing bottleneck.
- High completeness failures -> prioritize upstream mandatory-field controls.
- High aging -> review ownership/capacity.

Recommendations must be traceable to metrics and clearly labeled as analytical suggestions, not professional advice.

## UX

- Clear titles.
- Consistent filters.
- Empty states.
- Error handling.
- Last-refresh timestamp.
- Download filtered CSV where practical.

## Implemented usage

Run `streamlit run dashboard/app.py` and open localhost:8501. The six views share transaction date/business unit/team/source filters. Exception table and its charts additionally share local status/severity/priority/category/owner/root-cause/detection-date filters. The table leads with ID, status, severity, priority, rule and owner; the editor shows source lineage and permitted transitions.

Actions & Risks includes creation/update forms and dependency-aware completion. Management exports use the current sidebar scope; changing filters invalidates a previous report download. Details display up to 1,000 rows while the CSV includes all matches. Formula-like source strings are escaped for spreadsheet-safe export.

Charts distinguish current quality and persisted history. Exception and backlog trends group by transaction origination day; they do not claim historical stock or detection-event reconstruction. The Pareto includes cumulative share. Missing data shows N/A/empty states; all six views are tested with empty and seeded databases. API and UI share services, and the UI can run alone.
