"""KPI definitions and pure calculations shared by every output."""

import numpy as np
import pandas as pd

from app.core.config import Settings
from app.domain.rules import RULES, evaluate_rules, missing
from app.domain.time import age_days, aging_bucket

CATALOG = {
    "KPI001": (
        "Total Transactions",
        "count",
        "Count of transaction rows including duplicates and defective rows.",
    ),
    "KPI002": ("Processed Transactions", "count", "Count of rows with status Completed."),
    "KPI003": (
        "Open Backlog",
        "count",
        "Count of rows whose status is not Completed, including unknown statuses.",
    ),
    "KPI010": (
        "Completeness Rate",
        "rate",
        "Present mandatory observations / (6 × transaction rows).",
    ),
    "KPI011": (
        "Validity Rate",
        "rate",
        "Rows passing enabled Validity and Referential Integrity rules / transaction rows.",
    ),
    "KPI012": (
        "Duplicate Rate",
        "rate",
        "Duplicate IDs beyond the first nonblank occurrence / transaction rows.",
    ),
    "KPI013": (
        "Exception Rate",
        "rate",
        "Distinct transaction rows with persisted exceptions, including resolved history / transaction rows.",
    ),
    "KPI014": (
        "Overall Data Quality Score",
        "rate",
        "Configured weighted sum of completeness, validity, consistency, and timeliness rates; project methodology.",
    ),
    "KPI020": (
        "Average Processing TAT",
        "hours",
        "Mean nonnegative valid duration for Completed rows.",
    ),
    "KPI021": (
        "Median Processing TAT",
        "hours",
        "Median nonnegative valid duration for Completed rows.",
    ),
    "KPI022": (
        "SLA Compliance",
        "rate",
        "Completed rows with valid nonnegative duration ≤ configured SLA / eligible completed rows.",
    ),
    "KPI023": ("Rework Rate", "rate", "Completed rows with rework true / Completed rows."),
    "KPI030": ("Open Exceptions", "count", "Exceptions with status other than Resolved or Closed."),
    "KPI031": ("Critical Exceptions", "count", "Critical unresolved exceptions."),
    "KPI032": (
        "Exception Aging",
        "buckets",
        "Unresolved exceptions grouped by elapsed days since detection at simulation as-of.",
    ),
    "KPI033": (
        "Average Resolution Time",
        "hours",
        "Mean valid nonnegative hours from detection to resolution for Resolved/Closed exceptions.",
    ),
    "KPI040": ("Open Actions", "count", "Actions other than Completed or Cancelled."),
    "KPI041": (
        "Overdue Actions",
        "count",
        "Open actions with valid due timestamp earlier than simulation as-of.",
    ),
    "KPI042": (
        "Action Completion Rate",
        "rate",
        "Completed actions / all actions, including cancelled actions.",
    ),
    "KPI050": ("Open Risks", "count", "Risks whose status is not Closed."),
    "KPI051": (
        "High/Critical Risk Count",
        "count",
        "Open risks with probability × impact ≥ configured high-risk threshold.",
    ),
    "KPI052": (
        "Risk Exposure",
        "score",
        "Sum of probability × impact over open risks; ordinal score, not monetary exposure.",
    ),
}
MANDATORY = [
    "transaction_id",
    "account_id",
    "transaction_date",
    "amount",
    "currency",
    "business_unit_id",
]


def ratio(numerator: float, denominator: float) -> float | None:
    return float(numerator / denominator) if denominator else None


def quality_dimensions(tx: pd.DataFrame, masks: dict) -> dict:
    n = len(tx)
    completeness = ratio(sum(int((~missing(tx[c])).sum()) for c in MANDATORY), n * 6)
    rates = {"completeness": completeness}
    for dimension, categories in [
        ("validity", {"Validity", "Referential Integrity"}),
        ("consistency", {"Consistency"}),
        ("timeliness", {"Timeliness"}),
    ]:
        failures = pd.Series(False, index=tx.index)
        for rule in RULES:
            if rule.entity == "transaction" and rule.category in categories and rule.code in masks:
                failures |= masks[rule.code]
        rates[dimension] = ratio(n - int(failures.sum()), n)
    return rates


def enriched_transactions(tx: pd.DataFrame, policy: Settings) -> pd.DataFrame:
    frame = tx.copy()
    start = pd.to_datetime(frame.transaction_date, errors="coerce", utc=True, format="ISO8601")
    end = pd.to_datetime(frame.processing_date, errors="coerce", utc=True, format="ISO8601")
    frame["day"] = start.dt.strftime("%Y-%m-%d")
    frame["tat_hours"] = (end - start).dt.total_seconds() / 3600
    frame["eligible"] = (
        frame.status.eq("Completed") & frame.tat_hours.ge(0) & np.isfinite(frame.tat_hours)
    )
    frame["sla_met"] = frame.eligible & frame.tat_hours.le(policy.sla_hours)
    return frame


def calculate_kpis(bundle: dict, refs: dict, policy: Settings) -> dict:
    tx, ex, actions, risks = (bundle[k] for k in ["transactions", "exceptions", "actions", "risks"])
    as_of = bundle["as_of"]
    masks = evaluate_rules(tx, refs, policy, as_of)
    dimensions = quality_dimensions(tx, masks)
    frame = enriched_transactions(tx, policy)
    n = len(tx)
    processed = int(tx.status.eq("Completed").sum())
    open_ex = ex[~ex.status.isin(["Resolved", "Closed"])]
    open_actions = actions[~actions.status.isin(["Completed", "Cancelled"])]
    open_risks = risks[risks.status.ne("Closed")]
    eligible = frame[frame.eligible]
    aging = {
        aging_bucket(float(v), policy.aging_days): 0
        for v in [0, *[d + 0.01 for d in policy.aging_days]]
    }
    for detected in open_ex.detected_at:
        key = aging_bucket(age_days(detected, as_of), policy.aging_days)
        aging[key] = aging.get(key, 0) + 1
    resolved = ex[ex.status.isin(["Resolved", "Closed"])]
    resolution = (
        pd.to_datetime(resolved.resolved_at, errors="coerce", utc=True, format="ISO8601")
        - pd.to_datetime(resolved.detected_at, errors="coerce", utc=True, format="ISO8601")
    ).dt.total_seconds() / 3600
    resolution = resolution[resolution.ge(0) & np.isfinite(resolution)]
    values = {
        "KPI001": n,
        "KPI002": processed,
        "KPI003": n - processed,
        "KPI010": dimensions["completeness"],
        "KPI011": dimensions["validity"],
        "KPI012": ratio(
            int((~missing(tx.transaction_id) & tx.transaction_id.duplicated()).sum()), n
        ),
        "KPI013": ratio(ex.record_id[ex.record_id.isin(set(tx.id))].nunique(), n),
        "KPI014": sum(policy.weights[k] * dimensions[k] for k in dimensions) if n else None,
        "KPI020": float(eligible.tat_hours.mean()) if len(eligible) else None,
        "KPI021": float(eligible.tat_hours.median()) if len(eligible) else None,
        "KPI022": ratio(int(eligible.sla_met.sum()), len(eligible)),
        "KPI023": ratio(int((tx.status.eq("Completed") & tx.rework.eq(True)).sum()), processed),
        "KPI030": len(open_ex),
        "KPI031": int(open_ex.severity.eq("Critical").sum()),
        "KPI032": aging,
        "KPI033": float(resolution.mean()) if len(resolution) else None,
        "KPI040": len(open_actions),
        "KPI041": int(
            pd.to_datetime(open_actions.due_date, errors="coerce", utc=True, format="ISO8601")
            .lt(pd.Timestamp(as_of, tz="UTC"))
            .sum()
        ),
        "KPI042": ratio(int(actions.status.eq("Completed").sum()), len(actions)),
        "KPI050": len(open_risks),
        "KPI051": int(
            (open_risks.probability * open_risks.impact).ge(policy.high_risk_score).sum()
        ),
        "KPI052": int((open_risks.probability * open_risks.impact).sum()),
    }
    return {
        "values": values,
        "dimensions": dimensions,
        "metrics": [
            {
                "code": code,
                "name": name,
                "unit": unit,
                "definition": definition,
                "value": values[code],
            }
            for code, (name, unit, definition) in CATALOG.items()
        ],
        "context": {
            "as_of": as_of,
            "refresh_timestamp": bundle.get("ingested_at"),
            "source": bundle.get("source", "synthetic SQLite"),
            "filters": bundle.get("filters", {}),
            "period_from": frame.day.dropna().min() if frame.day.notna().any() else None,
            "period_to": frame.day.dropna().max() if frame.day.notna().any() else None,
            "eligible_completed": len(eligible),
            "excluded_completed": processed - len(eligible),
            "policy": policy.model_dump(mode="json"),
        },
    }
