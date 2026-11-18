# 5-Minute Demo Script

## 1. Introduce the problem
"Financial operations teams need reliable data, timely processing, and visibility into exceptions and remediation."

## 2. Show the architecture
Explain:
Synthetic data -> validation -> exception management -> KPI engine -> dashboard/reporting.

## 3. Show data quality
Demonstrate:
- completeness
- validity
- duplicates
- rule failures

## 4. Show operational KPIs
Explain:
- SLA compliance
- processing TAT
- backlog
- rework

## 5. Investigate an exception
Open an exception and show:
- rule
- severity
- priority
- root cause
- owner
- due date
- resolution

## 6. Show action/risk tracking
Demonstrate overdue actions and high risks.

## 7. Show executive reporting
Open the generated Excel/PDF report.

## 8. Explain business value
Close with:
"The project turns operational records into validated information, prioritized exceptions, management KPIs, and actionable improvement recommendations."

## Ready-to-run demonstration

Start with the README quick-start commands (or use the already seeded local database). Open localhost:8501 and API `/docs` at localhost:8000. Begin in Executive Overview, use Business unit/Source filters, then inspect Data Quality's source score and cumulative control Pareto. Explain current checks versus resolved history.

On Operational Performance, show TAT/SLA eligibility and the excluded Completed count, then compare teams/stages. On Exceptions, filter Critical, select an ID in Manage an exception, assign it, move to In Progress, add resolution notes and resolve. On Actions & Risks, demonstrate an owner, deadline, dependency, mitigation and risk score. Show Recommendations' metric evidence and export management reports.

Open `reports/examples/management.xlsx` and `reports/examples/executive.html`; explain synthetic data, simulated SLA/score and absence of cross-currency totals. Use `python -m app.cli validate` to demonstrate zero duplicate exceptions. The compact CSV/manifest in data/demo and automated tests provide inspectable control evidence.
