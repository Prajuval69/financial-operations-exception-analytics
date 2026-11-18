import pandas as pd
import pytest
from sqlalchemy import select

from app.db.models import ExceptionRecord
from app.domain.rules import RULES, evaluate_rules
from app.services.generator import GeneratorConfig, generate
from app.services.ingestion import seed_dataset
from app.services.reference import REFERENCE_DATA, reference_sets
from app.services.validation import run_validation

BASE = dict(
    transaction_id="TX1",
    account_id="ACC1",
    transaction_date="2026-09-29T10:00:00",
    processing_date="2026-09-29T12:00:00",
    amount="100",
    currency="USD",
    business_unit_id="BU01",
    transaction_type="Payment",
    status="Completed",
    priority="P2",
    team_id="TEAM01",
    source_system_id="SRC01",
)
REFS = {k: set(v) for k, v in REFERENCE_DATA.items()} | {"account_id": {"ACC1"}}
CASES = {
    "DQ001": {"transaction_id": None},
    "DQ002": {"account_id": ""},
    "DQ003": {"transaction_date": None},
    "DQ004": {"amount": None},
    "DQ005": {"currency": " "},
    "DQ006": {"business_unit_id": None},
    "DQ010": {"amount": "nan"},
    "DQ011": {"amount": "-1"},
    "DQ012": {"currency": "ZZZ"},
    "DQ013": {"transaction_type": "BAD"},
    "DQ014": {"status": "BAD"},
    "DQ015": {"priority": "P8"},
    "DQ016": {"business_unit_id": "BAD"},
    "DQ017": {"transaction_date": "bad"},
    "DQ018": {"processing_date": "bad"},
    "DQ019": {"processing_date": None},
    "DQ020": {"processing_date": "2026-09-28"},
    "DQ030": {},
    "DQ040": {"processing_date": "2026-09-28"},
    "DQ041": {"processing_date": "2026-09-30T13:00:00", "transaction_date": "2026-09-20"},
    "DQ050": {"account_id": "BAD"},
    "DQ051": {"team_id": "BAD"},
    "DQ052": {"source_system_id": None},
    "DQ060": {"amount": "2500000"},
}


@pytest.mark.parametrize("code,changes", CASES.items())
def test_each_transaction_rule(code, changes, policy):
    frame = pd.DataFrame([BASE, BASE | changes])
    masks = evaluate_rules(frame, REFS, policy, "2026-09-30T18:00:00")
    assert masks[code].tolist() == [False, True]


@pytest.mark.parametrize(
    "code,entity,bad,good",
    [
        (
            "DQ021",
            "exception",
            dict(status="Resolved", resolved_at=None, severity="Low", owner="A"),
            dict(resolved_at="2026-09-30"),
        ),
        (
            "DQ022",
            "action",
            dict(status="Completed", completed_at=None),
            dict(completed_at="2026-09-30"),
        ),
        (
            "DQ023",
            "exception",
            dict(status="Detected", severity="Critical", owner=None),
            dict(owner="A"),
        ),
    ],
)
def test_each_governance_rule(code, entity, bad, good, policy):
    frame = pd.DataFrame([bad | good, bad])
    assert evaluate_rules(frame, REFS, policy, "2026-09-30", entity)[code].tolist() == [False, True]


def test_all_catalog_rules_have_tests():
    assert {r.code for r in RULES} == set(CASES) | {"DQ021", "DQ022", "DQ023"}


def test_rule_configuration_and_boundaries(policy):
    frame = pd.DataFrame([BASE | {"amount": "1000000"}, BASE | {"amount": "inf"}])
    masks = evaluate_rules(frame, REFS, policy, "2026-09-30")
    assert not masks["DQ060"].any()
    assert masks["DQ010"].tolist() == [False, True]
    policy.disabled_rules = ["DQ010"]
    assert "DQ010" not in evaluate_rules(frame, REFS, policy, "2026-09-30")
    policy.date_tolerance_minutes = 5
    f = pd.DataFrame([BASE | {"processing_date": "2026-09-29T09:58:00"}])
    masks = evaluate_rules(f, REFS, policy, "2026-09-30")
    assert not masks["DQ020"].any() and masks["DQ040"].all()


def test_noniso_dates_and_missing_controlled_values(policy):
    frame = pd.DataFrame(
        [
            BASE
            | {
                "transaction_date": "09/29/2026",
                "transaction_type": None,
                "status": None,
                "priority": None,
            }
        ]
    )
    result = evaluate_rules(frame, REFS, policy, "2026-09-30")
    assert all(result[code].all() for code in ["DQ017", "DQ013", "DQ014", "DQ015"])


def test_injected_defects_detected_and_validation_idempotent(session, policy):
    config = GeneratorConfig(rows=1000, accounts=100)
    seed_dataset(session, config)
    _, _, manifest = generate(config)
    first = run_validation(session, policy)
    ex = list(session.scalars(select(ExceptionRecord)))
    detected = {(int(e.source_record_id), e.rule_code) for e in ex}
    assert all((entry["row_number"], entry["expected_rule"]) in detected for entry in manifest)
    assert first["new_exceptions"] > 120
    ex[0].status, ex[0].resolved_at, ex[0].resolution_notes = (
        "Resolved",
        config.as_of.isoformat(),
        "Reviewed",
    )
    session.flush()
    assert run_validation(session, policy)["new_exceptions"] == 0
    assert ex[0].status == "Resolved"
    assert all(e.owner for e in ex if e.severity in {"High", "Critical"})
    assert reference_sets(session)["account_id"]
