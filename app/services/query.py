"""Shared data access and filter scope used by API, UI, and reports."""

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Action, DatasetMeta, ExceptionRecord, ProcessingEvent, Risk, Transaction
from app.domain.time import now_iso


def serialize(model) -> dict:
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def table_frame(session: Session, model, statement=None) -> pd.DataFrame:
    statement = statement if statement is not None else select(model)
    statement = statement.with_only_columns(*model.__table__.columns)
    return pd.DataFrame(
        session.execute(statement).mappings().all(),
        columns=[c.name for c in model.__table__.columns],
    )


@dataclass(frozen=True)
class Filters:
    business_unit: str | None = None
    team: str | None = None
    status: str | None = None
    source_system: str | None = None
    date_from: str | None = None
    date_to: str | None = None

    def statement(self):
        query = select(Transaction).order_by(Transaction.id)
        for field, value in [
            ("business_unit_id", self.business_unit),
            ("team_id", self.team),
            ("status", self.status),
            ("source_system_id", self.source_system),
        ]:
            if value:
                query = query.where(getattr(Transaction, field) == value)
        if self.date_from:
            query = query.where(Transaction.transaction_day >= self.date_from)
        if self.date_to:
            query = query.where(Transaction.transaction_day <= self.date_to)
        return query


def load_bundle(session: Session, filters: Filters | None = None) -> dict:
    filters = filters or Filters()
    tx = table_frame(session, Transaction, filters.statement())
    ex = table_frame(session, ExceptionRecord)
    actions = table_frame(session, Action)
    risks = table_frame(session, Risk)
    events = table_frame(session, ProcessingEvent)
    scoped = any(v is not None for v in vars(filters).values())
    if scoped:
        ids = set(tx.id)
        ex = ex[ex.record_id.isin(ids)]
        ex_ids = set(ex.exception_id)
        actions = actions[actions.exception_id.isin(ex_ids)]
        risks = risks[
            risks.related_exception_id.isin(ex_ids) | risks.action_id.isin(set(actions.action_id))
        ]
        events = events[events.record_id.isin(ids)]
    meta = session.get(DatasetMeta, 1)
    return {
        "transactions": tx,
        "exceptions": ex,
        "actions": actions,
        "risks": risks,
        "events": events,
        "as_of": meta.as_of if meta else now_iso(),
        "ingested_at": meta.ingested_at if meta else None,
        "filters": vars(filters),
        "source": meta.source if meta else "empty database",
    }
