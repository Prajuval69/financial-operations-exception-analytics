"""Raw transaction fields stay nullable/text so bad inputs remain inspectable."""

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Reference(Base):
    __tablename__ = "reference_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    code: Mapped[str] = mapped_column(String(60))
    label: Mapped[str] = mapped_column(String(120))
    __table_args__ = (UniqueConstraint("kind", "code"),)


class Account(Base):
    __tablename__ = "accounts"
    account_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    account_type: Mapped[str] = mapped_column(String(40))
    business_unit_id: Mapped[str] = mapped_column(String(60))
    country: Mapped[str] = mapped_column(String(10))
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[str] = mapped_column(String(40))


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str | None] = mapped_column(String(80), index=True)
    account_id: Mapped[str | None] = mapped_column(String(60))
    business_unit_id: Mapped[str | None] = mapped_column(String(60), index=True)
    source_system_id: Mapped[str | None] = mapped_column(String(60), index=True)
    transaction_date: Mapped[str | None] = mapped_column(String(40), index=True)
    transaction_day: Mapped[str | None] = mapped_column(String(10), index=True)
    processing_date: Mapped[str | None] = mapped_column(String(40))
    transaction_type: Mapped[str | None] = mapped_column(String(40))
    amount: Mapped[str | None] = mapped_column(String(80))
    currency: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(String(40), index=True)
    priority: Mapped[str | None] = mapped_column(String(20))
    team_id: Mapped[str | None] = mapped_column(String(60), index=True)
    owner: Mapped[str | None] = mapped_column(String(100))
    reference_code: Mapped[str | None] = mapped_column(String(100))
    rework: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(40))
    updated_at: Mapped[str] = mapped_column(String(40))
    raw: Mapped[dict] = mapped_column(JSON, default=dict)


class ProcessingEvent(Base):
    __tablename__ = "processing_events"
    event_id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), index=True
    )
    transaction_id: Mapped[str | None] = mapped_column(String(80))
    stage: Mapped[str] = mapped_column(String(40))
    event_timestamp: Mapped[str] = mapped_column(String(40))
    team_id: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(40))
    duration_minutes: Mapped[float] = mapped_column(Float)
    exception_flag: Mapped[bool] = mapped_column(Boolean, default=False)


class ExceptionRecord(Base):
    __tablename__ = "exceptions"
    exception_id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), index=True
    )
    source_entity: Mapped[str] = mapped_column(String(30), default="transaction")
    source_record_id: Mapped[str] = mapped_column(String(80))
    transaction_id: Mapped[str | None] = mapped_column(String(80), index=True)
    rule_code: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    suggested_action: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    priority: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30), default="Detected", index=True)
    root_cause: Mapped[str] = mapped_column(String(60))
    business_impact: Mapped[str] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(100))
    detected_at: Mapped[str] = mapped_column(String(40))
    due_date: Mapped[str] = mapped_column(String(40))
    resolved_at: Mapped[str | None] = mapped_column(String(40))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("source_entity", "source_record_id", "rule_code"),)


class Action(Base):
    __tablename__ = "actions"
    action_id: Mapped[int] = mapped_column(primary_key=True)
    exception_id: Mapped[int | None] = mapped_column(ForeignKey("exceptions.exception_id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(100))
    priority: Mapped[str] = mapped_column(String(10), default="P2")
    due_date: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="Open")
    dependency: Mapped[int | None] = mapped_column(ForeignKey("actions.action_id"))
    created_at: Mapped[str] = mapped_column(String(40))
    completed_at: Mapped[str | None] = mapped_column(String(40))


class Risk(Base):
    __tablename__ = "risks"
    risk_id: Mapped[int] = mapped_column(primary_key=True)
    related_exception_id: Mapped[int | None] = mapped_column(ForeignKey("exceptions.exception_id"))
    action_id: Mapped[int | None] = mapped_column(ForeignKey("actions.action_id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    probability: Mapped[int] = mapped_column(Integer)
    impact: Mapped[int] = mapped_column(Integer)
    risk_score: Mapped[int] = mapped_column(Integer)
    owner: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="Open")
    mitigation: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[str] = mapped_column(String(40))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int] = mapped_column(Integer)
    occurred_at: Mapped[str] = mapped_column(String(40))
    changes: Mapped[dict] = mapped_column(JSON)


class ValidationRun(Base):
    __tablename__ = "validation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    as_of: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[str] = mapped_column(String(40))
    summary: Mapped[dict] = mapped_column(JSON)
    policy: Mapped[dict] = mapped_column(JSON)


class DatasetMeta(Base):
    __tablename__ = "dataset_meta"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    as_of: Mapped[str] = mapped_column(String(40))
    seed: Mapped[int | None] = mapped_column(Integer)
    ingested_at: Mapped[str] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(200))


Index("ix_exception_queue", ExceptionRecord.status, ExceptionRecord.severity)
