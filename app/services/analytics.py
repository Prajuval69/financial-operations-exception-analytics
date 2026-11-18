from collections import Counter

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import ValidationRun
from app.domain.kpis import calculate_kpis, enriched_transactions, quality_dimensions
from app.domain.rules import evaluate_rules
from app.services.query import Filters, load_bundle
from app.services.reference import reference_sets


def grouped_counts(frame: pd.DataFrame, field: str) -> list[dict]:
    return [
        {field: str(k), "count": int(v)}
        for k, v in frame[field].fillna("Missing").value_counts().items()
    ]


def derive_recommendations(kpis: dict) -> list[dict]:
    values = kpis["values"]
    candidates = [
        (
            "KPI012",
            lambda v: v >= 0.005,
            "Investigate duplicate submissions",
            "Add an idempotency check at source ingestion.",
            "P2",
        ),
        (
            "KPI022",
            lambda v: v < 0.95,
            "Review processing bottlenecks",
            "Use team and process-stage analysis to target SLA breaches.",
            "P1",
        ),
        (
            "KPI010",
            lambda v: v < 0.999,
            "Strengthen mandatory-field controls",
            "Validate required fields before accepting upstream batches.",
            "P2",
        ),
        (
            "KPI031",
            lambda v: v > 0,
            "Review critical reference exceptions",
            "Verify missing account mappings and assign remediation owners.",
            "P1",
        ),
        (
            "KPI041",
            lambda v: v > 0,
            "Clear overdue remediation",
            "Review dependencies and capacity for overdue actions.",
            "P1",
        ),
        (
            "KPI051",
            lambda v: v > 0,
            "Review high risk mitigations",
            "Connect high-scoring open risks to owned mitigation actions.",
            "P1",
        ),
    ]
    recommendations = []
    for code, trigger, title, action, priority in candidates:
        value = values[code]
        if value is not None and trigger(value):
            recommendations.append(
                {
                    "title": title,
                    "action": action,
                    "metric_code": code,
                    "observed_value": value,
                    "priority": priority,
                    "basis": kpis["context"]["as_of"],
                    "classification": "Analytical suggestion; project thresholds",
                }
            )
    old = sum(v for k, v in values["KPI032"].items() if k == ">30 days")
    if old:
        recommendations.append(
            {
                "title": "Review aging exception ownership",
                "action": "Review capacity and root causes for exceptions older than 30 days.",
                "metric_code": "KPI032",
                "observed_value": old,
                "priority": "P1",
                "basis": kpis["context"]["as_of"],
                "classification": "Analytical suggestion; project thresholds",
            }
        )
    return recommendations


def build_analytics(session: Session, policy: Settings, filters: Filters | None = None) -> dict:
    bundle = load_bundle(session, filters)
    refs = reference_sets(session)
    kpis = calculate_kpis(bundle, refs, policy)
    frame = enriched_transactions(bundle["transactions"], policy)
    ex = bundle["exceptions"]
    flagged_ids = set(ex.record_id.dropna())
    frame["has_exception"] = frame.id.isin(flagged_ids)
    masks = evaluate_rules(bundle["transactions"], refs, policy, bundle["as_of"])
    # Daily quality is recomputed from records rather than averaging segment percentages.
    quality_by = {}
    for field in ["source_system_id", "business_unit_id", "day"]:
        rows = []
        for key, group in frame.groupby(field, dropna=True, sort=True):
            dims = quality_dimensions(
                group, {code: mask.loc[group.index] for code, mask in masks.items()}
            )
            rows.append(
                {
                    field: str(key),
                    **dims,
                    "score": sum(policy.weights[k] * dims[k] for k in dims),
                    "rows": len(group),
                }
            )
        quality_by[field] = rows
    daily = []
    for day, group in frame.groupby("day", sort=True):
        eligible = group[group.eligible]
        daily.append(
            {
                "day": day,
                "transactions": len(group),
                "exceptions": int(group.has_exception.sum()),
                "backlog": int(group.status.ne("Completed").sum()),
                "sla_compliance": float(eligible.sla_met.mean()) if len(eligible) else None,
                "average_tat": float(eligible.tat_hours.mean()) if len(eligible) else None,
            }
        )
    teams = []
    for team, group in frame.groupby("team_id", dropna=False):
        eligible = group[group.eligible]
        teams.append(
            {
                "team": str(team) if pd.notna(team) else "Missing",
                "transactions": len(group),
                "backlog": int(group.status.ne("Completed").sum()),
                "eligible_completed": len(eligible),
                "sla_compliance": float(eligible.sla_met.mean()) if len(eligible) else None,
                "average_tat": float(eligible.tat_hours.mean()) if len(eligible) else None,
            }
        )
    events = bundle["events"]
    stages = [
        {
            "stage": stage,
            "events": len(group),
            "average_minutes": float(group.duration_minutes.mean()),
        }
        for stage, group in events.groupby("stage")
    ]
    run = session.scalar(select(ValidationRun).order_by(ValidationRun.id.desc()).limit(1))
    counts = Counter(ex.rule_code)
    return {
        "bundle": bundle,
        "kpis": kpis,
        "trends": daily,
        "teams": teams,
        "stages": stages,
        "quality_by": quality_by,
        "categories": grouped_counts(ex, "category"),
        "root_causes": grouped_counts(ex, "root_cause"),
        "rule_counts": [
            {"rule_code": code, "count": count} for code, count in counts.most_common()
        ],
        "validation": run.summary if run else None,
        "recommendations": derive_recommendations(kpis),
    }
