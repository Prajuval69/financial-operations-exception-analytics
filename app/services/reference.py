from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, Reference

REFERENCE_DATA = {
    "currency": {c: c for c in ["USD", "EUR", "GBP", "INR", "JPY", "SGD"]},
    "country": {c: c for c in ["US", "GB", "IN", "SG", "DE", "JP"]},
    "transaction_type": {c: c for c in ["Payment", "Settlement", "Transfer", "Reconciliation"]},
    "status": {c: c for c in ["Completed", "Pending", "In Progress", "Failed"]},
    "priority": {c: c for c in ["P1", "P2", "P3", "P4"]},
    "business_unit_id": {
        f"BU{i:02}": name
        for i, name in enumerate(
            [
                "Payments",
                "Custody",
                "Fund Services",
                "Markets",
                "Treasury",
                "Reconciliation",
                "Client Operations",
                "Corporate Services",
                "Transfer Agency",
                "Technology Operations",
            ],
            1,
        )
    },
    "team_id": {
        f"TEAM{i:02}": name
        for i, name in enumerate(
            [
                "Settlement Control",
                "Payments Processing",
                "Reconciliation Desk",
                "Data Operations",
                "Client Support",
                "Exception Management",
                "Reference Data",
                "Platform Support",
            ],
            1,
        )
    },
    "source_system_id": {
        f"SRC{i:02}": name
        for i, name in enumerate(
            [
                "Payment Gateway",
                "Settlement Hub",
                "Ledger Simulator",
                "Client Portal",
                "Batch Import",
                "Reference Feed",
            ],
            1,
        )
    },
    "exception_category": {
        c: c
        for c in [
            "Completeness",
            "Validity",
            "Consistency",
            "Duplicate",
            "Referential Integrity",
            "Timeliness",
            "Outlier",
            "Processing",
            "Reconciliation",
            "Governance",
        ]
    },
}


def seed_references(session: Session) -> None:
    existing = {(r.kind, r.code) for r in session.scalars(select(Reference))}
    session.add_all(
        [
            Reference(kind=kind, code=code, label=label)
            for kind, values in REFERENCE_DATA.items()
            for code, label in values.items()
            if (kind, code) not in existing
        ]
    )
    session.flush()


def reference_sets(session: Session) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {kind: set() for kind in REFERENCE_DATA}
    for value in session.scalars(select(Reference)):
        refs[value.kind].add(value.code)
    refs["account_id"] = set(session.scalars(select(Account.account_id)))
    return refs
