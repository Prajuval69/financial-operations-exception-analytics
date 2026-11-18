from app.db.models import Base
from app.domain.rules import RULES

DESCRIPTIONS = {
    "id": "Internal surrogate identity; source transaction IDs may be defective or repeated.",
    "record_id": "Internal transaction row identity; lineage remains unambiguous for duplicate source IDs.",
    "raw": "Original source values, retained for investigation before type coercion.",
    "amount": "Raw amount text; validation controls numeric conversion. No cross-currency monetary totals.",
    "transaction_date": "Source transaction timestamp; raw text preserves malformed dates for detection.",
    "transaction_day": "Derived valid transaction date in UTC for reliable SQL date filters; null for malformed or missing source dates.",
    "processing_date": "Source completion timestamp; missing for unprocessed rows.",
    "risk_score": "Ordinal probability × impact score; not monetary or institution-approved risk exposure.",
    "rework": "Synthetic flag that processing required rework.",
    "source_record_id": "Primary identity in source_entity, independent of defective external transaction ID.",
    "as_of": "Simulation timestamp used consistently for SLA, aging, and overdue calculations.",
    "ingested_at": "Actual UTC ingestion timestamp, distinct from simulation time.",
    "detected_at": "Detection timestamp; demo includes explicitly simulated historical detections.",
    "changes": "Audit field differences with before and after values.",
    "policy": "Validated rule thresholds and weights captured at validation time.",
    "summary": "Validation run counts by rule at the recorded simulation time.",
}
ALLOWED = {
    "probability": "Integer 1–5",
    "impact": "Integer 1–5",
    "risk_score": "Integer 1–25",
    "priority": "P1, P2, P3, P4",
    "severity": "Low, Medium, High, Critical",
    "rework": "true/false",
    "currency": "USD, EUR, GBP, INR, JPY, SGD (raw transactions may fail)",
    "status": "Entity lifecycle/reference values; raw transaction values are validated",
}


def data_dictionary() -> list[dict]:
    rows = []
    for table in Base.metadata.sorted_tables:
        entity = {
            "transactions": "transaction",
            "exceptions": "exception",
            "actions": "action",
        }.get(table.name)
        for col in table.columns:
            rules = [r.code for r in RULES if r.entity == entity and r.field == col.name]
            source = (
                "Synthetic generator / synthetic CSV"
                if table.name in {"transactions", "accounts"}
                else "Local application service"
            )
            rows.append(
                {
                    "entity": table.name,
                    "field": col.name,
                    "type": str(col.type),
                    "nullable": col.nullable,
                    "description": DESCRIPTIONS.get(
                        col.name, col.name.replace("_", " ").capitalize() + "."
                    ),
                    "allowed_values": ALLOWED.get(
                        col.name,
                        "ISO datetime for timestamp fields; see schema for other values"
                        if col.name.endswith(("_at", "_date"))
                        else "See entity schema/reference data",
                    ),
                    "example": "2026-09-30T18:00:00"
                    if col.name.endswith(("_at", "_date"))
                    else {
                        "amount": "125.50",
                        "currency": "USD",
                        "priority": "P2",
                        "severity": "High",
                        "probability": "3",
                        "impact": "4",
                        "rework": "false",
                    }.get(col.name, "1" if col.primary_key else "Synthetic value"),
                    "source": source,
                    "validation_rules": ", ".join(rules) or "Schema/service invariants",
                }
            )
    return rows
