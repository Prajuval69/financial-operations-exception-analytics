# Interview Q&A Preparation

## What problem does the project solve?
It provides visibility into data quality and operational performance by validating records, prioritizing exceptions, calculating KPIs, and tracking remediation.

## Why synthetic data?
Real financial operations data is confidential and unavailable for a portfolio project. Synthetic data allows realistic testing without exposing sensitive information.

## How do you detect data-quality problems?
Through deterministic validation rules covering completeness, validity, consistency, uniqueness, referential integrity, timeliness, and configurable outlier checks.

## How do you prioritize exceptions?
Severity reflects the nature/impact of the rule failure. Priority considers severity plus factors such as age, business impact, SLA status, and amount where relevant.

## Why Streamlit?
It provides a lightweight local dashboard that can be built and run without Power BI Desktop or external infrastructure.

## What would you change for production?
Use enterprise authentication, governed data sources, stronger access control, production databases, orchestration, observability, data lineage, formal control approval, CI/CD, and institution-specific business rules.

## What is the biggest limitation?
The project uses synthetic data and simulated operational policies, so it demonstrates engineering and analytical capability rather than production financial processing.
