import pandas as pd
import pytest
from sqlalchemy import select

from app.api.schemas import ActionCreate, ActionPatch, ExceptionPatch, RiskCreate, RiskPatch
from app.db.models import Action, AuditEvent, ExceptionRecord, Risk
from app.domain.kpis import CATALOG, calculate_kpis
from app.domain.priority import calculate_priority
from app.domain.time import age_days, aging_bucket
from app.services.analytics import build_analytics, derive_recommendations
from app.services.generator import GeneratorConfig
from app.services.ingestion import seed_dataset
from app.services.validation import run_validation
from app.services.workflow import (
    ConflictError,
    create_action,
    create_risk,
    seed_demo_workflow,
    update_action,
    update_exception,
    update_risk,
)
from tests.test_rules import BASE, REFS


@pytest.fixture
def golden_bundle():
    tx = pd.DataFrame(
        [
            BASE | {"id": 1, "rework": True},
            BASE | {"id": 2, "processing_date": "2026-10-01T12:00:00", "rework": False},
            BASE
            | {
                "id": 3,
                "transaction_id": "TX3",
                "amount": "-5",
                "processing_date": "2026-09-29T09:00:00",
                "rework": False,
            },
            BASE
            | {
                "id": 4,
                "transaction_id": "TX4",
                "amount": None,
                "status": "Pending",
                "transaction_date": "2026-09-30T17:00:00",
                "processing_date": None,
                "rework": False,
            },
        ]
    )
    ex = pd.DataFrame(
        [
            dict(
                exception_id=1,
                record_id=1,
                status="Detected",
                severity="High",
                detected_at="2026-09-29T18:00:00",
                resolved_at=None,
            ),
            dict(
                exception_id=2,
                record_id=2,
                status="Assigned",
                severity="Critical",
                detected_at="2026-08-21T18:00:00",
                resolved_at=None,
            ),
            dict(
                exception_id=3,
                record_id=3,
                status="Resolved",
                severity="High",
                detected_at="2026-09-25T18:00:00",
                resolved_at="2026-09-26T18:00:00",
            ),
            dict(
                exception_id=4,
                record_id=1,
                status="Closed",
                severity="High",
                detected_at="2026-09-28T18:00:00",
                resolved_at="2026-09-29T18:00:00",
            ),
        ]
    )
    actions = pd.DataFrame(
        [
            dict(status="Completed", due_date="2026-09-28"),
            dict(status="Open", due_date="2026-09-28"),
            dict(status="In Progress", due_date="2026-10-10"),
            dict(status="Cancelled", due_date="2026-09-28"),
        ]
    )
    risks = pd.DataFrame(
        [
            dict(status="Open", probability=3, impact=4),
            dict(status="Mitigating", probability=2, impact=2),
            dict(status="Closed", probability=5, impact=5),
        ]
    )
    return dict(
        transactions=tx, exceptions=ex, actions=actions, risks=risks, as_of="2026-09-30T18:00:00"
    )


EXPECTED = {
    "KPI001": 4,
    "KPI002": 3,
    "KPI003": 1,
    "KPI010": 23 / 24,
    "KPI011": 0.75,
    "KPI012": 0.25,
    "KPI013": 0.75,
    "KPI014": 0.7625,
    "KPI020": 26,
    "KPI021": 26,
    "KPI022": 0.5,
    "KPI023": 1 / 3,
    "KPI030": 2,
    "KPI031": 1,
    "KPI033": 24,
    "KPI040": 2,
    "KPI041": 1,
    "KPI042": 0.25,
    "KPI050": 2,
    "KPI051": 1,
    "KPI052": 16,
}


@pytest.mark.parametrize("code,value", EXPECTED.items())
def test_every_scalar_kpi_formula(golden_bundle, policy, code, value):
    result = calculate_kpis(golden_bundle, REFS, policy)
    assert result["values"][code] == pytest.approx(value)


def test_aging_and_kpi_catalog(golden_bundle, policy):
    result = calculate_kpis(golden_bundle, REFS, policy)
    assert result["values"]["KPI032"]["0–2 days"] == 1
    assert result["values"]["KPI032"][">30 days"] == 1
    assert set(CATALOG) == set(EXPECTED) | {"KPI032"}
    assert result["context"]["excluded_completed"] == 1
    assert age_days("2026-10-01", "2026-09-30") == 0
    assert aging_bucket(2, [2, 7]) == "0–2 days"
    assert aging_bucket(2.1, [2, 7]) == "2–7 days"


@pytest.mark.parametrize(
    "severity,age,amount,sla,impact,expected",
    [
        ("Critical", 0, 1, False, "", "P1"),
        ("High", 0, 1, False, "", "P2"),
        ("Medium", 0, 1, False, "", "P3"),
        ("Low", 0, 1, False, "", "P4"),
        ("Medium", 8, 2500000, True, "Material reporting risk", "P1"),
        ("Low", 8, 1, False, "", "P3"),
    ],
)
def test_priority_policy(policy, severity, age, amount, sla, impact, expected):
    assert calculate_priority(severity, age, amount, sla, impact, policy) == expected


def test_recommendations_trace_observed_metrics(golden_bundle, policy):
    kpis = calculate_kpis(golden_bundle, REFS, policy)
    recs = derive_recommendations(kpis)
    assert len(recs) == 7
    assert {r["metric_code"] for r in recs} <= set(CATALOG)
    for r in recs:
        if r["metric_code"] != "KPI032":
            assert r["observed_value"] == kpis["values"][r["metric_code"]]


def test_empty_database_analytics(session, policy):
    result = build_analytics(session, policy)
    assert result["kpis"]["values"]["KPI001"] == 0
    assert result["kpis"]["values"]["KPI022"] is None
    assert result["kpis"]["values"]["KPI014"] is None
    assert not result["recommendations"] and not result["trends"]


@pytest.fixture
def seeded(session, policy):
    seed_dataset(session, GeneratorConfig(rows=500, accounts=50))
    run_validation(session, policy)
    return session


def test_workflow_transitions_and_audit(seeded):
    ex = seeded.scalar(select(ExceptionRecord))
    with pytest.raises(ConflictError):
        update_exception(seeded, ex.exception_id, ExceptionPatch(status="Closed"))
    for status in ["Assigned", "In Progress"]:
        update_exception(seeded, ex.exception_id, ExceptionPatch(status=status))
    with pytest.raises(ValueError, match="notes"):
        update_exception(seeded, ex.exception_id, ExceptionPatch(status="Resolved"))
    update_exception(
        seeded,
        ex.exception_id,
        ExceptionPatch(status="Resolved", resolution_notes="Corrected mapping"),
    )
    assert ex.resolved_at
    update_exception(seeded, ex.exception_id, ExceptionPatch(status="Closed"))
    update_exception(seeded, ex.exception_id, ExceptionPatch(status="Reopened"))
    assert ex.resolved_at is None
    assert len(list(seeded.scalars(select(AuditEvent)))) == 5


def test_action_dependencies_and_risk_score(seeded):
    a = create_action(
        seeded, ActionCreate(title="Verify source", owner="Desk", due_date="2026-10-01T00:00:00")
    )
    b = create_action(
        seeded,
        ActionCreate(
            title="Review control",
            owner="Desk",
            due_date="2026-10-02T00:00:00",
            dependency=a.action_id,
        ),
    )
    with pytest.raises(ConflictError, match="cycle"):
        update_action(seeded, a.action_id, ActionPatch(dependency=b.action_id))
    with pytest.raises(ConflictError, match="dependency"):
        update_action(seeded, b.action_id, ActionPatch(status="Completed"))
    update_action(seeded, a.action_id, ActionPatch(status="Completed"))
    update_action(seeded, b.action_id, ActionPatch(status="Completed"))
    assert b.completed_at
    risk = create_risk(
        seeded,
        RiskCreate(
            title="Control risk",
            owner="Desk",
            due_date="2026-10-01T00:00:00",
            probability=3,
            impact=4,
            action_id=b.action_id,
        ),
    )
    assert risk.risk_score == 12
    update_risk(seeded, risk.risk_id, RiskPatch(probability=5))
    assert risk.risk_score == 20
    update_action(seeded, b.action_id, ActionPatch(status="Open"))
    assert b.completed_at is None


def test_demo_workflow_is_idempotent(seeded, policy):
    first = seed_demo_workflow(seeded)
    assert first["actions"] > 0 and first["risks"] == 30
    assert seed_demo_workflow(seeded) == {"actions": 0, "risks": 0}
    analytics = build_analytics(seeded, policy)
    assert analytics["kpis"]["values"]["KPI041"] > 0
    assert sum(d["transactions"] for d in analytics["trends"]) <= 500
    assert len(list(seeded.scalars(select(Action)))) == first["actions"]
    assert len(list(seeded.scalars(select(Risk)))) == 30


def test_root_cause_and_severity_configuration(session, policy):
    from app.domain.rules import ROOT_CAUSES

    seed_dataset(session, GeneratorConfig(rows=1000, accounts=100))
    policy.severity_overrides = {"DQ060": "Critical"}
    run_validation(session, policy)
    for exception in session.scalars(select(ExceptionRecord)):
        assert exception.root_cause == ROOT_CAUSES[exception.category]
        if exception.rule_code == "DQ060":
            assert exception.severity == "Critical" and exception.priority == "P1"


def test_custom_validation_clock_updates_kpi_context(seeded, policy):
    result = run_validation(seeded, policy, "2026-10-01T18:00:00")
    assert build_analytics(seeded, policy)["kpis"]["context"]["as_of"] == result["as_of"]
