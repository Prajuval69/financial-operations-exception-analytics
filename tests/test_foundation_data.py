import pandas as pd
import pytest
from sqlalchemy import func, select

from app.core.config import Settings
from app.db.models import Account, ProcessingEvent, Transaction
from app.services.generator import GeneratorConfig, generate
from app.services.ingestion import ingest_csv, ingest_frame, seed_dataset


def test_policy_rejects_bad_weights_and_rules():
    with pytest.raises(ValueError):
        Settings(weights={"completeness": 1})
    with pytest.raises(ValueError):
        Settings(disabled_rules=["DQ999"])
    with pytest.raises(ValueError):
        Settings(aging_days=[7, 2])
    with pytest.raises(ValueError):
        Settings(high_value_threshold=float("inf"))
    with pytest.raises(ValueError):
        Settings(
            weights={
                "completeness": float("nan"),
                "validity": 0.3,
                "consistency": 0.2,
                "timeliness": 0.2,
            }
        )


def test_deterministic_generator():
    config = GeneratorConfig(rows=500, accounts=50)
    a, accounts, manifest = generate(config)
    b, accounts2, manifest2 = generate(config)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(accounts, accounts2)
    assert manifest == manifest2 and len(manifest) == 60
    c, _, _ = generate(config.model_copy(update={"seed": 43}))
    assert not a.equals(c)


def test_database_seed_roundtrip(session, tmp_path):
    result = seed_dataset(session, GeneratorConfig(rows=100, accounts=10), tmp_path)
    assert (
        result["transactions"]
        == session.scalar(select(func.count()).select_from(Transaction))
        == 100
    )
    assert session.scalar(select(func.count()).select_from(Account)) == 10
    assert session.scalar(select(func.count()).select_from(ProcessingEvent)) > 100
    assert (tmp_path / "defect_manifest.json").exists()
    with pytest.raises(ValueError, match="already exists"):
        ingest_frame(session, generate(GeneratorConfig(rows=1))[0], "2026-09-30", "test")


def test_invalid_csv(session, tmp_path):
    file = tmp_path / "bad.csv"
    file.write_text("amount\n123\n")
    with pytest.raises(ValueError, match="missing columns"):
        ingest_csv(session, file, "2026-09-30")


def test_invalid_generation_parameters():
    for value in [0, -1, 1_000_001]:
        with pytest.raises(ValueError):
            GeneratorConfig(rows=value)


def test_timezone_normalization_and_date_filter(session):
    from app.db.models import DatasetMeta
    from app.services.query import Filters
    from tests.test_rules import BASE

    frame = pd.DataFrame(
        [
            BASE | {"transaction_date": "2026-09-30T01:00:00+05:30"},
            BASE | {"transaction_id": "TX2", "transaction_date": "bad"},
        ]
    )
    ingest_frame(session, frame, "2026-09-30T23:30:00+05:30", "test")
    assert session.get(DatasetMeta, 1).as_of == "2026-09-30T18:00:00"
    rows = list(session.scalars(Filters(date_from="2026-09-29", date_to="2026-09-29").statement()))
    assert len(rows) == 1 and rows[0].transaction_day == "2026-09-29"


def test_additive_schema_upgrade(engine):
    from sqlalchemy import inspect, text

    from app.db.session import init_db

    with engine.begin() as connection:
        connection.execute(text("DROP INDEX ix_transactions_transaction_day"))
        connection.execute(text("ALTER TABLE transactions DROP COLUMN transaction_day"))
    init_db(engine)
    assert "transaction_day" in {c["name"] for c in inspect(engine).get_columns("transactions")}
    init_db(engine)
