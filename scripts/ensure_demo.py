"""Container bootstrap: preserve existing datasets, seed only an empty database."""

from sqlalchemy import func, select

from app.cli import main
from app.db.models import Transaction
from app.db.session import init_db, make_engine, session_scope

engine = make_engine()
init_db(engine)
with session_scope(engine) as session:
    exists = session.scalar(select(func.count()).select_from(Transaction))
engine.dispose()
if not exists:
    raise SystemExit(main(["demo"]))
print("Existing synthetic dataset preserved.")
