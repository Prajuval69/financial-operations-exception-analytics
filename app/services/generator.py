"""Seeded synthetic simulator with a deterministic defect manifest."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator

from app.services.reference import REFERENCE_DATA


class GeneratorConfig(BaseModel):
    rows: int = Field(default=50_000, ge=1, le=1_000_000)
    accounts: int = Field(default=5_000, ge=1, le=100_000)
    seed: int = Field(default=42, ge=0)
    as_of: datetime = datetime(2026, 9, 30, 18)
    defect_rate: float = Field(default=0.12, ge=0, le=0.5)

    @field_validator("as_of")
    @classmethod
    def utc_clock(cls, value: datetime) -> datetime:
        from app.domain.time import parse_date

        return parse_date(value.isoformat())


def generate(config: GeneratorConfig) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    rng = np.random.default_rng(config.seed)
    end = config.as_of.replace(tzinfo=None)
    account_rows = []
    for i in range(config.accounts):
        account_rows.append(
            {
                "account_id": f"ACC{i + 1:06}",
                "account_type": ["Institutional", "Corporate", "Custody"][i % 3],
                "business_unit_id": f"BU{i % 10 + 1:02}",
                "country": list(REFERENCE_DATA["country"])[i % 6],
                "currency": list(REFERENCE_DATA["currency"])[i % 6],
                "status": "Active",
                "created_at": (end - timedelta(days=365)).isoformat(),
            }
        )
    rows = []
    for i in range(config.rows):
        account = account_rows[int(rng.integers(0, config.accounts))]
        start = end - timedelta(hours=float(rng.uniform(1, 90 * 24)))
        completed = rng.random() < 0.87
        duration = float(np.clip(rng.lognormal(2.1, 0.7), 0.25, 44))
        processing = min(end, start + timedelta(hours=duration)) if completed else None
        # Open records are recent except those deliberately injected as SLA failures.
        if not completed:
            start = end - timedelta(hours=float(rng.uniform(1, 44)))
        rows.append(
            {
                "transaction_id": f"TX{i + 1:08}",
                "account_id": account["account_id"],
                "business_unit_id": account["business_unit_id"],
                "source_system_id": f"SRC{int(rng.integers(1, 7)):02}",
                "transaction_date": start.isoformat(timespec="seconds"),
                "processing_date": processing.isoformat(timespec="seconds") if processing else None,
                "transaction_type": rng.choice(list(REFERENCE_DATA["transaction_type"])).item(),
                "amount": f"{min(float(rng.lognormal(8, 1.4)), 900000):.2f}",
                "currency": account["currency"],
                "status": "Completed"
                if completed
                else rng.choice(["Pending", "In Progress", "Failed"]).item(),
                "priority": rng.choice(["P1", "P2", "P3", "P4"], p=[0.05, 0.2, 0.5, 0.25]).item(),
                "team_id": f"TEAM{int(rng.integers(1, 9)):02}",
                "owner": f"Analyst {i % 24 + 1:02}",
                "reference_code": f"REF-{i + 1:08}",
                "rework": bool(rng.random() < 0.05),
                "created_at": start.isoformat(timespec="seconds"),
                "updated_at": end.isoformat(),
            }
        )
    kinds = [
        "missing_id",
        "missing_account",
        "missing_date",
        "missing_amount",
        "missing_currency",
        "missing_unit",
        "nonnumeric",
        "negative",
        "currency",
        "type",
        "status",
        "priority",
        "unit",
        "chronology",
        "duplicate",
        "late",
        "account",
        "team",
        "source",
        "outlier",
        "invalid_date",
        "invalid_processing",
        "missing_processing",
    ]
    expected = [
        "DQ001",
        "DQ002",
        "DQ003",
        "DQ004",
        "DQ005",
        "DQ006",
        "DQ010",
        "DQ011",
        "DQ012",
        "DQ013",
        "DQ014",
        "DQ015",
        "DQ016",
        "DQ020",
        "DQ030",
        "DQ041",
        "DQ050",
        "DQ051",
        "DQ052",
        "DQ060",
        "DQ017",
        "DQ018",
        "DQ019",
    ]
    selected = sorted(
        rng.choice(config.rows, int(config.rows * config.defect_rate), replace=False).tolist()
    )
    manifest = []
    for n, i in enumerate(selected):
        row = rows[i]
        kind = kinds[n % len(kinds)]
        if kind.startswith("missing_") and kind != "missing_processing":
            field = {
                "missing_id": "transaction_id",
                "missing_account": "account_id",
                "missing_date": "transaction_date",
                "missing_amount": "amount",
                "missing_currency": "currency",
                "missing_unit": "business_unit_id",
            }[kind]
            row[field] = None
        elif kind in {"nonnumeric", "negative", "outlier"}:
            row["amount"] = {
                "nonnumeric": "BAD_AMOUNT",
                "negative": "-125.00",
                "outlier": "2500000.00",
            }[kind]
        elif kind in {
            "currency",
            "type",
            "status",
            "priority",
            "unit",
            "account",
            "team",
            "source",
        }:
            field = {
                "currency": "currency",
                "type": "transaction_type",
                "status": "status",
                "priority": "priority",
                "unit": "business_unit_id",
                "account": "account_id",
                "team": "team_id",
                "source": "source_system_id",
            }[kind]
            row[field] = "UNKNOWN"
        elif kind in {"chronology", "late"}:
            start = end - timedelta(days=10)
            row.update(
                transaction_date=start.isoformat(),
                processing_date=(
                    start + timedelta(hours=-3 if kind == "chronology" else 96)
                ).isoformat(),
                status="Completed",
            )
        elif kind == "duplicate":
            original = next(r for j, r in enumerate(rows) if j != i and r["transaction_id"])
            row["transaction_id"] = original["transaction_id"]
        elif kind == "invalid_date":
            row["transaction_date"] = "NOT_A_DATE"
        elif kind == "invalid_processing":
            row["processing_date"] = "NOT_A_DATE"
        elif kind == "missing_processing":
            row.update(processing_date=None, status="Completed")
        manifest.append(
            {"row_number": i + 1, "defect": kind, "expected_rule": expected[n % len(kinds)]}
        )
    return pd.DataFrame(rows), pd.DataFrame(account_rows), manifest
