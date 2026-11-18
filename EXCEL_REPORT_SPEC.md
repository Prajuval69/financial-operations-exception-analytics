# Excel Reporting Specification

Generate an `.xlsx` workbook with openpyxl.

## Required sheets

1. Executive Summary
2. KPI Summary
3. Data Quality
4. Exceptions
5. Operational Performance
6. Actions
7. Risks
8. Raw/Processed Data sample
9. Data Dictionary
10. Methodology

## Formatting

- Freeze header rows.
- Autofilter tables.
- Sensible column widths.
- Number formats.
- Dates formatted consistently.
- Percentages displayed as percentages.
- Currency amounts displayed with currency code where useful.
- Use conditional formatting for status/severity where practical.
- Do not hardcode dashboard numbers; populate from calculated results.

## Executive Summary

Include:
- reporting period
- data refresh timestamp
- KPI table
- top five findings
- top five recommendations
- open critical items

## Methodology

Document:
- KPI formulas
- validation rules
- configurable thresholds
- assumptions
- synthetic-data limitations

## Implemented output

`python -m app.cli report excel` generates all ten sheets, using `Raw Processed Data Sample` as the Excel-compatible sample-sheet name. The sample is capped at 1,000 transactions; other workflow sheets contain all scoped rows. Percentages are numeric fractions with percentage formats. Headers freeze/filter, dates use consistent formats, severity/risk scores receive conditional formatting, and Operational Performance includes a native volume chart. Source text is escaped against spreadsheet-formula execution.

API and dashboard exports use their current sidebar/query scope. Examples: `reports/examples/management.xlsx`. Dictionary content is generated from the same ORM schema as the application. Quality rows and persisted-rule history are explicitly labeled. Methodology includes all formulas/controls, policy, eligibility and limitations.
