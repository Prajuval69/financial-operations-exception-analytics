from sqlalchemy import select

from app.api.schemas import ActionCreate
from app.db.models import ExceptionRecord, Transaction
from app.services.generator import GeneratorConfig
from app.services.ingestion import seed_dataset
from app.services.validation import run_validation
from app.services.workflow import create_action


def test_source_correction_auto_resolves_and_governance_is_persisted(session, policy):
    seed_dataset(session, GeneratorConfig(rows=1000, accounts=100))
    run_validation(session, policy)
    item = session.scalar(select(ExceptionRecord).where(ExceptionRecord.rule_code == "DQ010"))
    row = session.get(Transaction, item.record_id)
    row.amount = "125.00"
    action = create_action(
        session,
        ActionCreate(
            exception_id=item.exception_id,
            title="Correct source",
            owner="Desk",
            due_date="2026-10-07",
        ),
    )
    # Simulate corrupt legacy workflow data that the normal API would reject.
    action.status, action.completed_at = "Completed", None
    session.flush()
    run_validation(session, policy)
    assert item.status == "Resolved" and item.resolved_at
    finding = session.scalar(select(ExceptionRecord).where(ExceptionRecord.rule_code == "DQ022"))
    assert finding.source_entity == "action" and finding.source_record_id == str(action.action_id)
    assert finding.record_id == item.record_id
    action.completed_at = "2026-09-30T18:00:00"
    session.flush()
    run_validation(session, policy)
    assert finding.status == "Resolved"
