"""Refresh checked-in compact data and management examples from the local demo."""

import json
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.db.session import make_engine, session_scope
from app.reports.service import generate_excel, generate_executive
from app.services.analytics import build_analytics
from app.services.generator import GeneratorConfig, generate


def main() -> None:
    directory = Path("data/demo")
    directory.mkdir(parents=True, exist_ok=True)
    config = GeneratorConfig(rows=1000, accounts=100)
    transactions, accounts, manifest = generate(config)
    transactions.to_csv(directory / "transactions.csv", index=False)
    accounts.to_csv(directory / "accounts.csv", index=False)
    (directory / "defect_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (directory / "configuration.json").write_text(
        config.model_dump_json(indent=2), encoding="utf-8"
    )
    policy = get_settings()
    engine = make_engine(policy)
    with session_scope(engine) as session:
        analytics = build_analytics(session, policy)
    engine.dispose()
    output = Path("reports/examples")
    output.mkdir(parents=True, exist_ok=True)
    paths = [
        generate_excel(analytics, policy.output_dir),
        generate_executive(analytics, policy.output_dir),
    ]
    for source, name in zip(paths, ["management.xlsx", "executive.html"], strict=True):
        shutil.copyfile(source, output / name)
    (output / "kpi_snapshot.json").write_text(
        json.dumps(analytics["kpis"], indent=2), encoding="utf-8"
    )
    print("Compact sample: 1,000 rows. Management examples refreshed from the current database.")


if __name__ == "__main__":
    main()
