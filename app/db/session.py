from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.models import Base


def make_engine(settings: Settings | None = None) -> Engine:
    url = (settings or get_settings()).database_url
    if not url.startswith("sqlite:"):
        raise ValueError("This local release supports SQLite database URLs only")
    if url.startswith("sqlite:///") and url != "sqlite:///:memory:":
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"poolclass": StaticPool} if url == "sqlite:///:memory:" else {}
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30}, **kwargs)

    @event.listens_for(engine, "connect")
    def pragmas(connection, _record) -> None:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")

    return engine


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    # Additive v1 upgrade for checkouts created before UTC day filtering was introduced.
    if "transaction_day" not in {c["name"] for c in inspect(engine).get_columns("transactions")}:
        from app.domain.time import parse_date

        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE transactions ADD COLUMN transaction_day VARCHAR(10)")
            )
            records = connection.execute(
                text("SELECT id, transaction_date FROM transactions")
            ).all()
            updates = [
                {
                    "id": row.id,
                    "day": parsed.date().isoformat()
                    if (parsed := parse_date(row.transaction_date))
                    else None,
                }
                for row in records
            ]
            if updates:
                connection.execute(
                    text("UPDATE transactions SET transaction_day=:day WHERE id=:id"), updates
                )
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_transactions_transaction_day ON transactions (transaction_day)"
            )
        )


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
