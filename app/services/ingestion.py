import json
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.db.models import Account, DatasetMeta, ProcessingEvent, Transaction
from app.domain.time import now_iso, parse_date
from app.services.generator import GeneratorConfig, generate
from app.services.reference import seed_references

log = logging.getLogger(__name__)
REQUIRED_COLUMNS = {
    "transaction_id",
    "account_id",
    "transaction_date",
    "amount",
    "currency",
    "business_unit_id",
    "team_id",
    "source_system_id",
    "status",
    "priority",
    "transaction_type",
}


def ingest_frame(
    session: Session, frame: pd.DataFrame, as_of: str, source: str, seed: int | None = None
) -> int:
    parsed_as_of = parse_date(as_of)
    if parsed_as_of is None:
        raise ValueError("as_of must be an ISO timestamp")
    as_of = parsed_as_of.isoformat()
    if REQUIRED_COLUMNS - set(frame.columns):
        raise ValueError(
            f"CSV is missing columns: {', '.join(sorted(REQUIRED_COLUMNS - set(frame.columns)))}"
        )
    if session.scalar(select(func.count()).select_from(Transaction)):
        raise ValueError(
            "Dataset already exists. Use a fresh database or the explicit reset command."
        )
    if frame.empty:
        raise ValueError("Dataset contains no transaction rows")
    seed_references(session)
    known = {c.name for c in Transaction.__table__.columns} - {"id", "raw"}
    records, events = [], []
    for i, raw in enumerate(frame.to_dict("records"), 1):
        clean = {k: (None if pd.isna(v) else v) for k, v in raw.items()}
        rework = str(clean.get("rework", "false")).lower()
        if rework not in {"true", "false", "1", "0", "none", ""}:
            raise ValueError(f"Row {i}: rework must be true/false or 1/0")
        record = {
            k: str(v) if v is not None else None
            for k, v in clean.items()
            if k in known and k != "rework"
        }
        record.update(
            id=i,
            rework=rework in {"true", "1"},
            created_at=clean.get("created_at") or as_of,
            updated_at=clean.get("updated_at") or as_of,
            raw=clean,
        )
        records.append(record)
        start, end = (
            parse_date(record.get("transaction_date")),
            parse_date(record.get("processing_date")),
        )
        record["transaction_day"] = start.date().isoformat() if start else None
        if start and end and end >= start:
            minutes = (end - start).total_seconds() / 60
            for stage, fraction in [("Intake", 0.15), ("Control", 0.35), ("Settlement", 0.5)]:
                events.append(
                    {
                        "record_id": i,
                        "transaction_id": record.get("transaction_id"),
                        "stage": stage,
                        "event_timestamp": end.isoformat(),
                        "team_id": record.get("team_id"),
                        "status": record.get("status") or "Unknown",
                        "duration_minutes": minutes * fraction,
                        "exception_flag": record["rework"],
                    }
                )
    for start in range(0, len(records), 2000):
        session.execute(insert(Transaction), records[start : start + 2000])
    for start in range(0, len(events), 2000):
        session.execute(insert(ProcessingEvent), events[start : start + 2000])
    session.add(DatasetMeta(id=1, as_of=as_of, seed=seed, ingested_at=now_iso(), source=source))
    session.flush()
    log.info("ingested rows=%s processing_events=%s source=%s", len(records), len(events), source)
    return len(records)


def seed_dataset(session: Session, config: GeneratorConfig, export_dir: Path | None = None) -> dict:
    transactions, accounts, manifest = generate(config)
    session.execute(insert(Account), accounts.to_dict("records"))
    count = ingest_frame(
        session, transactions, config.as_of.isoformat(), "synthetic-generator", config.seed
    )
    if export_dir:
        export_dir.mkdir(parents=True, exist_ok=True)
        transactions.to_csv(export_dir / "transactions.csv", index=False)
        accounts.to_csv(export_dir / "accounts.csv", index=False)
        (export_dir / "defect_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
    return {
        "transactions": count,
        "accounts": len(accounts),
        "injected_defects": len(manifest),
        "seed": config.seed,
    }


def ingest_csv(session: Session, path: Path, as_of: str, accounts_path: Path | None = None) -> int:
    if path.stat().st_size > 250 * 1024 * 1024:
        raise ValueError("CSV exceeds the 250 MiB local ingestion limit")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if len(frame) > 1_000_000:
        raise ValueError("CSV exceeds the one million row limit")
    if accounts_path:
        accounts = pd.read_csv(accounts_path, dtype=str, keep_default_na=False)
        required = {c.name for c in Account.__table__.columns}
        if required - set(accounts):
            raise ValueError("Account CSV does not match the data dictionary")
        if accounts.account_id.eq("").any() or accounts.account_id.duplicated().any():
            raise ValueError("Account IDs must be present and unique")
        session.execute(insert(Account), accounts[list(required)].to_dict("records"))
    return ingest_frame(session, frame, as_of, "local-synthetic-csv")
