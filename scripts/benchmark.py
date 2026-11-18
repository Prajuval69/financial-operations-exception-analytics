"""Reproducible 100k-row measurement using an isolated temporary SQLite database."""

import argparse
import json
import platform
import tempfile
from pathlib import Path
from time import perf_counter

from app.core.config import Settings
from app.db.session import init_db, make_engine, session_scope
from app.services.analytics import build_analytics
from app.services.generator import GeneratorConfig
from app.services.ingestion import seed_dataset
from app.services.validation import run_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--output", type=Path, default=Path("docs/benchmark.json"))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="finops-benchmark-") as directory:
        policy = Settings(database_url=f"sqlite:///{(Path(directory) / 'benchmark.db').as_posix()}")
        engine = make_engine(policy)
        init_db(engine)
        result = {
            "rows": args.rows,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "seed": 42,
            "simulation_as_of": "2026-09-30T18:00:00",
        }
        with session_scope(engine) as session:
            start = perf_counter()
            seed_dataset(session, GeneratorConfig(rows=args.rows))
            result["generation_ingestion_seconds"] = round(perf_counter() - start, 3)
            start = perf_counter()
            validation = run_validation(session, policy)
            result["validation_seconds"] = round(perf_counter() - start, 3)
            result["exceptions"] = validation["new_exceptions"]
            start = perf_counter()
            analytics = build_analytics(session, policy)
            result["analytics_seconds"] = round(perf_counter() - start, 3)
            assert analytics["kpis"]["values"]["KPI001"] == args.rows
        engine.dispose()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
