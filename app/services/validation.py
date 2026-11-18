import logging
from datetime import timedelta

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Action, DatasetMeta, ExceptionRecord, Transaction, ValidationRun
from app.domain.priority import calculate_priority
from app.domain.rules import ROOT_CAUSES, RULES, evaluate_rules
from app.domain.time import age_days, now_iso, parse_date
from app.services.query import table_frame
from app.services.reference import reference_sets

log = logging.getLogger(__name__)


def run_validation(session: Session, policy: Settings, as_of: str | None = None) -> dict:
    meta = session.get(DatasetMeta, 1)
    as_of = as_of or (meta.as_of if meta else now_iso())
    end = parse_date(as_of)
    if end is None:
        raise ValueError("as_of must be a valid ISO timestamp")
    as_of = end.isoformat()
    if meta:
        meta.as_of = as_of
    refs = reference_sets(session)
    frames = {
        "transaction": table_frame(session, Transaction),
        "exception": table_frame(session, ExceptionRecord),
        "action": table_frame(session, Action),
    }
    known = {
        (e.source_entity, e.source_record_id, e.rule_code): e
        for e in session.scalars(select(ExceptionRecord))
    }
    failures, rule_counts, active = [], {}, set()
    for entity, frame in frames.items():
        masks = evaluate_rules(frame, refs, policy, as_of, entity)
        for rule in RULES:
            if rule.entity != entity or rule.code not in masks:
                continue
            mask = masks[rule.code]
            rule_counts[rule.code] = int(mask.sum())
            for row in frame[mask].to_dict("records"):
                pk = {"transaction": "id", "exception": "exception_id", "action": "action_id"}[
                    entity
                ]
                source_id = str(row[pk])
                key = (entity, source_id, rule.code)
                active.add(key)
                severity = policy.severity_overrides.get(rule.code, rule.severity)
                impact = (
                    "Material reporting risk"
                    if severity == "Critical"
                    else "Operational reporting reliability"
                )
                amount = pd.to_numeric(row.get("amount"), errors="coerce")
                amount = None if pd.isna(amount) else float(amount)
                if key in known:
                    item = known[key]
                    item.severity = severity
                    item.priority = calculate_priority(
                        severity,
                        age_days(item.detected_at, as_of),
                        amount,
                        rule.code == "DQ041",
                        impact,
                        policy,
                    )
                    continue
                record_id = row["id"] if entity == "transaction" else row.get("record_id")
                if entity == "action" and row.get("exception_id"):
                    linked = session.get(ExceptionRecord, int(row["exception_id"]))
                    record_id = linked.record_id if linked else None
                failures.append(
                    {
                        "record_id": record_id,
                        "source_entity": entity,
                        "source_record_id": source_id,
                        "transaction_id": row.get("transaction_id"),
                        "rule_code": rule.code,
                        "category": rule.category,
                        "description": rule.description,
                        "suggested_action": rule.suggested_action,
                        "severity": severity,
                        "priority": calculate_priority(
                            severity, 0, amount, rule.code == "DQ041", impact, policy
                        ),
                        "status": "Detected",
                        "root_cause": ROOT_CAUSES.get(rule.category, "Unknown"),
                        "business_impact": impact,
                        "owner": row.get("owner") or "Control Desk",
                        "detected_at": as_of,
                        "due_date": (
                            end
                            + timedelta(
                                days={"Critical": 1, "High": 2, "Medium": 7, "Low": 14}[severity]
                            )
                        ).isoformat(),
                        "resolved_at": None,
                        "resolution_notes": None,
                    }
                )
    for start in range(0, len(failures), 2000):
        session.execute(insert(ExceptionRecord), failures[start : start + 2000])
    # Corrected source controls can be resolved automatically; disabled controls stay untouched.
    for key, item in known.items():
        if (
            key not in active
            and item.rule_code not in policy.disabled_rules
            and item.status not in {"Resolved", "Closed"}
        ):
            item.status, item.resolved_at, item.resolution_notes = (
                "Resolved",
                as_of,
                "Source now passes this validation rule.",
            )
    summary = {
        "transaction_count": len(frames["transaction"]),
        "new_exceptions": len(failures),
        "failed_checks": sum(rule_counts.values()),
        "rule_counts": rule_counts,
        "as_of": as_of,
    }
    session.add(
        ValidationRun(
            as_of=as_of,
            created_at=now_iso(),
            summary=summary,
            policy=policy.model_dump(mode="json"),
        )
    )
    session.flush()
    log.info(
        "validation completed rows=%s failures=%s new=%s",
        summary["transaction_count"],
        summary["failed_checks"],
        len(failures),
    )
    return summary
