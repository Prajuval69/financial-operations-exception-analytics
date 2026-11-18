# Executive Report Specification

Generate a professional PDF or HTML report from the latest seeded/calculated data.

## Sections

1. Title
2. Executive Summary
3. Operational KPI Scorecard
4. Data Quality Assessment
5. Exception Analysis
6. Operational Trends
7. Risks and Actions
8. Key Findings
9. Recommendations
10. Methodology and Limitations

## Requirements

- Include generated date/time.
- Include reporting period.
- Include charts.
- Keep prose concise and executive-ready.
- Recommendations must be traceable to observed metrics.
- Clearly state that data is synthetic.
- Avoid claims that results represent real State Street operations.

## Implemented output

`python -m app.cli report executive` generates self-contained HTML, selected from the allowed PDF/HTML alternatives. Embedded Plotly enables offline interactive volume/SLA/category/source-quality charts. The report includes all specified sections, all 22 KPIs, source/period/filter/as-of/refresh/generation context and metric-linked recommendations. Detail tables truncate at 20 with an explicit count label. Browser print can produce a PDF; direct PDF generation is not required by this release.

Example: `reports/examples/executive.html`. All source prose is HTML-escaped. The report separates project scoring and simulated telemetry from institutional policy and real observations.
