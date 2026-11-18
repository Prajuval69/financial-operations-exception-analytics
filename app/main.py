"""FastAPI application factory, injectable database and policy for isolated tests."""

import logging
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.schemas import (
    ActionCreate,
    ActionPatch,
    ActionStatus,
    ExceptionPatch,
    ExceptionStatus,
    Priority,
    RiskCreate,
    RiskPatch,
    RiskStatus,
    ValidationInput,
)
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.models import Action, AuditEvent, ExceptionRecord, Reference, Risk, Transaction
from app.db.session import init_db, make_engine, session_scope
from app.services.analytics import build_analytics
from app.services.query import Filters, serialize
from app.services.validation import run_validation
from app.services.workflow import (
    ConflictError,
    NotFoundError,
    create_action,
    create_risk,
    get_entity,
    update_action,
    update_exception,
    update_risk,
)

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, engine=None) -> FastAPI:
    policy = settings or get_settings()
    db_engine = engine or make_engine(policy)

    @asynccontextmanager
    async def lifespan(_app):
        configure_logging()
        init_db(db_engine)
        yield
        if engine is None:
            db_engine.dispose()

    application = FastAPI(
        title="Financial Operations Quality & Exception Analytics",
        version="1.0.0",
        description="Synthetic local portfolio platform. No real financial data.",
        lifespan=lifespan,
    )
    application.state.engine = db_engine

    def database():
        with session_scope(db_engine) as session:
            yield session

    def filters(
        business_unit: str | None = None,
        team: str | None = None,
        status: str | None = None,
        source_system: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        if date_from and date_to and date_from > date_to:
            raise HTTPException(422, "date_from must not be after date_to")
        return Filters(
            business_unit,
            team,
            status,
            source_system,
            date_from.isoformat() if date_from else None,
            date_to.isoformat() if date_to else None,
        )

    @application.exception_handler(NotFoundError)
    async def missing_handler(_request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @application.exception_handler(ValueError)
    async def value_handler(_request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @application.exception_handler(Exception)
    async def unexpected_handler(_request: Request, exc: Exception):
        log.error("request failed type=%s", type(exc).__name__)
        return JSONResponse(
            status_code=500, content={"detail": "Operation failed. Check the local service logs."}
        )

    def paginate(session, query, page, page_size):
        total = session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
        items = [
            serialize(r)
            for r in session.scalars(query.offset((page - 1) * page_size).limit(page_size))
        ]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @application.get("/health")
    def health(session: Session = Depends(database)):
        session.execute(text("SELECT 1"))
        return {"status": "ok", "synthetic_data_only": True, "version": "1.0.0"}

    @application.get("/api/v1/references")
    def references(session: Session = Depends(database)):
        return [
            serialize(r)
            for r in session.scalars(select(Reference).order_by(Reference.kind, Reference.code))
        ]

    @application.get("/api/v1/transactions")
    def transactions(
        scope: Filters = Depends(filters),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=500),
        session: Session = Depends(database),
    ):
        return paginate(session, scope.statement(), page, page_size)

    @application.get("/api/v1/transactions/{transaction_id}")
    def transaction(transaction_id: str, session: Session = Depends(database)):
        rows = list(
            session.scalars(
                select(Transaction).where(Transaction.transaction_id == transaction_id).limit(2)
            )
        )
        if not rows:
            raise NotFoundError("Transaction was not found")
        if len(rows) > 1:
            raise ConflictError(
                "Duplicate source transaction ID. Use the paginated list and internal record IDs."
            )
        return serialize(rows[0])

    @application.post("/api/v1/validation/run")
    def validate(
        payload: ValidationInput = ValidationInput(), session: Session = Depends(database)
    ):
        from app.domain.time import parse_date

        return run_validation(
            session,
            policy,
            parse_date(payload.as_of.isoformat()).isoformat() if payload.as_of else None,
        )

    @application.get("/api/v1/validation/summary")
    def validation_summary(scope: Filters = Depends(filters), session: Session = Depends(database)):
        result = build_analytics(session, policy, scope)
        return {
            "latest_run": result["validation"],
            "scoped_persisted_rule_counts": result["rule_counts"],
            "quality_dimensions": result["kpis"]["dimensions"],
            "context": result["kpis"]["context"],
        }

    @application.get("/api/v1/exceptions")
    def exceptions(
        status: ExceptionStatus | None = None,
        severity: Literal["Low", "Medium", "High", "Critical"] | None = None,
        priority: Priority | None = None,
        category: str | None = None,
        owner: str | None = None,
        root_cause: str | None = None,
        team: str | None = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=500),
        session: Session = Depends(database),
    ):
        query = select(ExceptionRecord).order_by(ExceptionRecord.exception_id)
        for field, value in [
            ("status", status),
            ("severity", severity),
            ("priority", priority),
            ("category", category),
            ("owner", owner),
            ("root_cause", root_cause),
        ]:
            if value is not None:
                query = query.where(getattr(ExceptionRecord, field) == value)
        if team:
            query = query.where(
                ExceptionRecord.record_id.in_(
                    select(Transaction.id).where(Transaction.team_id == team)
                )
            )
        return paginate(session, query, page, page_size)

    @application.get("/api/v1/exceptions/{exception_id}")
    def exception_detail(exception_id: int, session: Session = Depends(database)):
        return serialize(get_entity(session, ExceptionRecord, exception_id))

    @application.patch("/api/v1/exceptions/{exception_id}")
    def exception_patch(
        exception_id: int, payload: ExceptionPatch, session: Session = Depends(database)
    ):
        return serialize(update_exception(session, exception_id, payload))

    @application.get("/api/v1/actions")
    def actions(
        status: ActionStatus | None = None,
        owner: str | None = None,
        priority: Priority | None = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=500),
        session: Session = Depends(database),
    ):
        query = select(Action).order_by(Action.action_id)
        for key, value in [("status", status), ("owner", owner), ("priority", priority)]:
            if value:
                query = query.where(getattr(Action, key) == value)
        return paginate(session, query, page, page_size)

    @application.post("/api/v1/actions", status_code=201)
    def action_create(payload: ActionCreate, session: Session = Depends(database)):
        return serialize(create_action(session, payload))

    @application.patch("/api/v1/actions/{action_id}")
    def action_patch(action_id: int, payload: ActionPatch, session: Session = Depends(database)):
        return serialize(update_action(session, action_id, payload))

    @application.get("/api/v1/risks")
    def risks(
        status: RiskStatus | None = None,
        owner: str | None = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=500),
        session: Session = Depends(database),
    ):
        query = select(Risk).order_by(Risk.risk_id)
        if status:
            query = query.where(Risk.status == status)
        if owner:
            query = query.where(Risk.owner == owner)
        return paginate(session, query, page, page_size)

    @application.post("/api/v1/risks", status_code=201)
    def risk_create(payload: RiskCreate, session: Session = Depends(database)):
        return serialize(create_risk(session, payload))

    @application.patch("/api/v1/risks/{risk_id}")
    def risk_patch(risk_id: int, payload: RiskPatch, session: Session = Depends(database)):
        return serialize(update_risk(session, risk_id, payload))

    @application.get("/api/v1/kpis/summary")
    def kpis(scope: Filters = Depends(filters), session: Session = Depends(database)):
        return build_analytics(session, policy, scope)["kpis"]

    @application.get("/api/v1/kpis/trends")
    def trends(scope: Filters = Depends(filters), session: Session = Depends(database)):
        result = build_analytics(session, policy, scope)
        return {"items": result["trends"], "context": result["kpis"]["context"]}

    @application.get("/api/v1/kpis/exceptions")
    def exception_analytics(
        scope: Filters = Depends(filters), session: Session = Depends(database)
    ):
        result = build_analytics(session, policy, scope)
        return {
            key: result[key]
            for key in ["categories", "root_causes", "rule_counts", "recommendations"]
        } | {"aging": result["kpis"]["values"]["KPI032"]}

    @application.get("/api/v1/kpis/teams")
    def team_analytics(scope: Filters = Depends(filters), session: Session = Depends(database)):
        result = build_analytics(session, policy, scope)
        return {
            "items": result["teams"],
            "stages": result["stages"],
            "context": result["kpis"]["context"],
        }

    @application.get("/api/v1/audit")
    def audit_events(
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=500),
        session: Session = Depends(database),
    ):
        return paginate(session, select(AuditEvent).order_by(AuditEvent.id.desc()), page, page_size)

    @application.post("/api/v1/reports/{report_type}")
    def report(
        report_type: Literal["excel", "executive"],
        scope: Filters = Depends(filters),
        session: Session = Depends(database),
    ):
        from app.reports.service import generate_excel, generate_executive

        result = build_analytics(session, policy, scope)
        path = (generate_excel if report_type == "excel" else generate_executive)(
            result, policy.output_dir
        )
        return FileResponse(path, filename=path.name)

    return application


app = create_app()
