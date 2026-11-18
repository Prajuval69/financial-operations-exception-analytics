"""State transitions and owned remediation with audit history."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ActionCreate, ActionPatch, ExceptionPatch, RiskCreate, RiskPatch
from app.db.models import Action, AuditEvent, DatasetMeta, ExceptionRecord, Risk, Transaction
from app.domain.time import now_iso, parse_date
from app.services.query import serialize

log = logging.getLogger(__name__)

TRANSITIONS = {
    "Detected": {"Assigned"},
    "Assigned": {"In Progress"},
    "In Progress": {"Resolved"},
    "Resolved": {"Closed", "Reopened"},
    "Closed": {"Reopened"},
    "Reopened": {"Assigned", "In Progress"},
}
ACTION_TRANSITIONS = {
    "Open": {"In Progress", "Blocked", "Completed", "Cancelled"},
    "In Progress": {"Blocked", "Completed", "Cancelled"},
    "Blocked": {"In Progress", "Cancelled"},
    "Completed": {"Open"},
    "Cancelled": {"Open"},
}


class NotFoundError(ValueError):
    pass


class ConflictError(ValueError):
    pass


def clock_for(session: Session) -> str:
    meta = session.get(DatasetMeta, 1)
    return meta.as_of if meta else now_iso()


def get_entity(session: Session, model, entity_id: int):
    item = session.get(model, entity_id)
    if item is None:
        raise NotFoundError(f"{model.__name__} {entity_id} was not found")
    return item


def normalized_changes(schema) -> dict:
    changes = schema.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if isinstance(value, datetime):
            changes[key] = parse_date(value.isoformat()).isoformat()
    return changes


def audit(session: Session, item, before: dict | None = None) -> None:
    session.flush()
    after = serialize(item)
    changes = {
        k: {"before": (before or {}).get(k), "after": v}
        for k, v in after.items()
        if (before or {}).get(k) != v
    }
    pk = item.__table__.primary_key.columns.values()[0].name
    session.add(
        AuditEvent(
            entity=item.__tablename__,
            entity_id=getattr(item, pk),
            occurred_at=now_iso(),
            changes=changes,
        )
    )
    log.debug(
        "workflow entity=%s id=%s changed_fields=%s",
        item.__tablename__,
        getattr(item, pk),
        list(changes),
    )


def update_exception(session: Session, entity_id: int, patch: ExceptionPatch) -> ExceptionRecord:
    item = get_entity(session, ExceptionRecord, entity_id)
    before = serialize(item)
    changes = normalized_changes(patch)
    status = changes.get("status", item.status)
    owner = changes.get("owner", item.owner)
    if status is None or changes.get("priority", item.priority) is None:
        raise ValueError("Status and priority cannot be null")
    if status != item.status and status not in TRANSITIONS[item.status]:
        raise ConflictError(f"Cannot move exception from {item.status} to {status}")
    if (
        item.severity in {"High", "Critical"} or status in {"Assigned", "In Progress"}
    ) and not owner:
        raise ValueError("An owner is required for this exception")
    if (
        status in {"Resolved", "Closed"}
        and not (changes.get("resolution_notes", item.resolution_notes) or "").strip()
    ):
        raise ValueError("Resolution notes are required")
    for key, value in changes.items():
        setattr(item, key, value)
    if status == "Resolved" and before["status"] != status:
        item.resolved_at = clock_for(session)
    if status == "Reopened":
        item.resolved_at = None
    audit(session, item, before)
    return item


def check_dependency(
    session: Session, dependency: int | None, action_id: int | None = None
) -> None:
    seen = {action_id} if action_id else set()
    while dependency is not None:
        if dependency in seen:
            raise ConflictError("Action dependencies must not contain a cycle")
        seen.add(dependency)
        dependency = get_entity(session, Action, dependency).dependency


def create_action(session: Session, payload: ActionCreate) -> Action:
    changes = normalized_changes(payload)
    if payload.exception_id:
        get_entity(session, ExceptionRecord, payload.exception_id)
    check_dependency(session, payload.dependency)
    item = Action(**changes, status="Open", created_at=clock_for(session))
    session.add(item)
    audit(session, item)
    return item


def update_action(session: Session, entity_id: int, patch: ActionPatch) -> Action:
    item = get_entity(session, Action, entity_id)
    before = serialize(item)
    changes = normalized_changes(patch)
    if any(v is None for k, v in changes.items() if k != "dependency"):
        raise ValueError("Action fields cannot be null except dependency")
    check_dependency(session, changes.get("dependency", item.dependency), entity_id)
    status = changes.get("status", item.status)
    if status != item.status and status not in ACTION_TRANSITIONS[item.status]:
        raise ConflictError(f"Cannot move action from {item.status} to {status}")
    dependency = changes.get("dependency", item.dependency)
    if (
        status == "Completed"
        and dependency
        and get_entity(session, Action, dependency).status != "Completed"
    ):
        raise ConflictError("Complete the dependency before completing this action")
    for key, value in changes.items():
        setattr(item, key, value)
    item.completed_at = (item.completed_at or clock_for(session)) if status == "Completed" else None
    audit(session, item, before)
    return item


def create_risk(session: Session, payload: RiskCreate) -> Risk:
    if payload.related_exception_id:
        get_entity(session, ExceptionRecord, payload.related_exception_id)
    if payload.action_id:
        get_entity(session, Action, payload.action_id)
    item = Risk(
        **normalized_changes(payload),
        risk_score=payload.probability * payload.impact,
        status="Open",
    )
    session.add(item)
    audit(session, item)
    return item


def update_risk(session: Session, entity_id: int, patch: RiskPatch) -> Risk:
    item = get_entity(session, Risk, entity_id)
    before = serialize(item)
    changes = normalized_changes(patch)
    if any(v is None for k, v in changes.items() if k != "action_id"):
        raise ValueError("Risk fields cannot be null except action_id")
    if changes.get("action_id"):
        get_entity(session, Action, changes["action_id"])
    for key, value in changes.items():
        setattr(item, key, value)
    item.risk_score = item.probability * item.impact
    audit(session, item, before)
    return item


def seed_demo_workflow(session: Session) -> dict:
    """Explicit simulated history, created only by the demo command."""
    from datetime import timedelta

    if session.scalar(select(Action.action_id).limit(1)):
        return {"actions": 0, "risks": 0}
    as_of = parse_date(clock_for(session))
    exceptions = list(
        session.scalars(select(ExceptionRecord).order_by(ExceptionRecord.exception_id))
    )
    transaction_dates = dict(
        session.execute(select(Transaction.id, Transaction.transaction_date)).all()
    )
    for i, item in enumerate(exceptions):
        before = serialize(item)
        source_date = parse_date(transaction_dates.get(item.record_id))
        historical = as_of - timedelta(days=i % 40)
        item.detected_at = min(as_of, max(historical, source_date or historical)).isoformat()
        item.due_date = (
            parse_date(item.detected_at)
            + timedelta(days=2 if item.severity in {"Critical", "High"} else 7)
        ).isoformat()
        if i % 5 == 0:
            item.status, item.resolved_at, item.resolution_notes = (
                "Resolved",
                (parse_date(item.detected_at) + timedelta(hours=12)).isoformat(),
                "Synthetic analyst reviewed source defect; remediation history is simulated.",
            )
            if parse_date(item.resolved_at) > as_of:
                item.resolved_at = as_of.isoformat()
        audit(session, item, before)
    action_count, risk_count = 0, 0
    for i, ex in enumerate(exceptions[:80]):
        action = create_action(
            session,
            ActionCreate(
                exception_id=ex.exception_id,
                title=f"Remediate {ex.rule_code} control failure",
                description=ex.suggested_action,
                owner=ex.owner or "Control Desk",
                priority=ex.priority,
                due_date=as_of + timedelta(days=i % 15 - 5),
            ),
        )
        if i % 4 == 0:
            update_action(session, action.action_id, ActionPatch(status="Completed"))
        action_count += 1
        if i < 30:
            create_risk(
                session,
                RiskCreate(
                    related_exception_id=ex.exception_id,
                    action_id=action.action_id,
                    title=f"Recurring {ex.category.lower()} control exposure",
                    description=ex.description,
                    probability=i % 5 + 1,
                    impact=(i * 3) % 5 + 1,
                    owner=ex.owner or "Control Desk",
                    mitigation="Review source controls and complete the linked remediation.",
                    due_date=as_of + timedelta(days=i % 20),
                ),
            )
            risk_count += 1
    return {"actions": action_count, "risks": risk_count}
