"""Common local operations: python -m app.cli --help."""

import argparse
import json
import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.models import Base, Transaction
from app.db.session import init_db, make_engine, session_scope
from app.domain.time import parse_date
from app.reports.service import generate_excel, generate_executive
from app.services.analytics import build_analytics
from app.services.dictionary import data_dictionary
from app.services.generator import GeneratorConfig
from app.services.ingestion import ingest_csv, seed_dataset
from app.services.reference import REFERENCE_DATA, seed_references
from app.services.validation import run_validation
from app.services.workflow import seed_demo_workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic financial operations analytics")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db", help="Initialize schema and controlled reference values")
    for name in ["seed", "demo"]:
        command = commands.add_parser(
            name,
            help="Generate synthetic records"
            if name == "seed"
            else "Seed, validate, simulate workflow and generate both reports",
        )
        command.add_argument("--rows", type=int, default=50000)
        command.add_argument("--accounts", type=int, default=5000)
        command.add_argument("--seed", type=int, default=42)
        command.add_argument("--as-of", default="2026-09-30T18:00:00")
        command.add_argument("--defect-rate", type=float, default=0.12)
        command.add_argument("--export-dir", type=Path, default=Path("data/raw"))
    validate = commands.add_parser(
        "validate", help="Validate without duplicating existing exceptions"
    )
    validate.add_argument("--as-of", default=None)
    ingest = commands.add_parser(
        "ingest", help="Ingest a local synthetic CSV into an empty dataset"
    )
    ingest.add_argument("path", type=Path)
    ingest.add_argument("--accounts", type=Path)
    ingest.add_argument("--as-of", required=True)
    ingest.add_argument(
        "--synthetic",
        action="store_true",
        required=True,
        help="Confirm this file contains synthetic data only",
    )
    reports = commands.add_parser(
        "report", help="Generate a workbook or self-contained executive HTML"
    )
    reports.add_argument("kind", choices=["excel", "executive", "all"], default="all", nargs="?")
    commands.add_parser("kpis", help="Print calculated KPI summary")
    commands.add_parser(
        "dictionary", help="Regenerate synchronized data dictionary and reference JSON"
    )
    reset = commands.add_parser("reset-db", help="Remove all local records and recreate schema")
    reset.add_argument(
        "--yes", action="store_true", required=True, help="Explicitly acknowledge database reset"
    )
    args = parser.parse_args(argv)
    configure_logging()
    policy = get_settings()
    engine = make_engine(policy)
    try:
        init_db(engine)
        if args.command == "reset-db":
            Base.metadata.drop_all(engine)
            init_db(engine)
            result = {"status": "database reset"}
        elif args.command == "dictionary":
            import pandas as pd

            rows = data_dictionary()
            Path("docs").mkdir(exist_ok=True)
            pd.DataFrame(rows).to_csv("docs/data_dictionary.csv", index=False)
            lines = [
                "# Data Dictionary",
                "",
                "Generated from SQLAlchemy schema by `python -m app.cli dictionary`.",
                "",
                "| Entity | Field | Type | Nullable | Description | Allowed values | Example | Source | Validation |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
            lines += [
                "| "
                + " | ".join(
                    str(r[k]).replace("|", "/")
                    for k in [
                        "entity",
                        "field",
                        "type",
                        "nullable",
                        "description",
                        "allowed_values",
                        "example",
                        "source",
                        "validation_rules",
                    ]
                )
                + " |"
                for r in rows
            ]
            Path("DATA_DICTIONARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            Path("data/reference").mkdir(parents=True, exist_ok=True)
            Path("data/reference/reference_values.json").write_text(
                json.dumps(REFERENCE_DATA, indent=2), encoding="utf-8"
            )
            result = {"fields": len(rows), "dictionary": "DATA_DICTIONARY.md"}
        else:
            with session_scope(engine) as session:
                if args.command == "init-db":
                    seed_references(session)
                    result = {"status": "initialized"}
                elif args.command in {"seed", "demo"}:
                    if session.scalar(select(func.count()).select_from(Transaction)):
                        raise ValueError(
                            "Dataset exists; choose another FINOPS_DATABASE_URL or explicitly reset-db --yes."
                        )
                    end = parse_date(args.as_of)
                    if end is None:
                        raise ValueError("--as-of must be an ISO datetime")
                    config = GeneratorConfig(
                        rows=args.rows,
                        accounts=args.accounts,
                        seed=args.seed,
                        as_of=end,
                        defect_rate=args.defect_rate,
                    )
                    result = seed_dataset(session, config, args.export_dir)
                    if args.command == "demo":
                        result["validation"] = run_validation(session, policy)
                        result["workflow"] = seed_demo_workflow(session)
                        # Refresh priorities after generating historical detection timestamps.
                        run_validation(session, policy)
                        analytics = build_analytics(session, policy)
                        result["reports"] = [
                            str(generate_excel(analytics, policy.output_dir)),
                            str(generate_executive(analytics, policy.output_dir)),
                        ]
                elif args.command == "ingest":
                    result = {"rows": ingest_csv(session, args.path, args.as_of, args.accounts)}
                elif args.command == "validate":
                    result = run_validation(session, policy, args.as_of)
                else:
                    analytics = build_analytics(session, policy)
                    if args.command == "kpis":
                        result = analytics["kpis"]
                    else:
                        result = {"reports": []}
                        if args.kind in {"excel", "all"}:
                            result["reports"].append(
                                str(generate_excel(analytics, policy.output_dir))
                            )
                        if args.kind in {"executive", "all"}:
                            result["reports"].append(
                                str(generate_executive(analytics, policy.output_dir))
                            )
        print(json.dumps(result, indent=2, default=str))
        return 0
    except (ValueError, OSError) as error:
        logging.getLogger(__name__).error("command failed: %s", error)
        return 1
    except SQLAlchemyError:
        logging.getLogger(__name__).error(
            "Database operation failed. Check database permissions, schema and input uniqueness."
        )
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
