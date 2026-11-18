"""Verify installation and demo workflow in a temporary clean source copy."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from time import perf_counter


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = {"checks": []}
    with tempfile.TemporaryDirectory(prefix="finops-clean-") as directory:
        checkout = Path(directory) / "checkout"
        excluded = shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "*.egg-info",
            "*.db*",
            ".env",
            "*.log",
            ".coverage",
        )

        def ignore(source, names):
            ignored = set(excluded(source, names))
            if Path(source).resolve() == root:
                ignored.add("reports")
            if Path(source).resolve() == root / "data":
                ignored.add("raw")
            return ignored

        shutil.copytree(root, checkout, ignore=ignore)
        commands = [
            ["uv", "sync", "--frozen", "--extra", "dev"],
            ["uv", "run", "--frozen", "--extra", "dev", "ruff", "check", "."],
            ["uv", "run", "--frozen", "--extra", "dev", "ruff", "format", "--check", "."],
            ["uv", "run", "--frozen", "--extra", "dev", "pytest", "-q", "--tb=short"],
            [
                "uv",
                "run",
                "--frozen",
                "--extra",
                "dev",
                "python",
                "-m",
                "app.cli",
                "demo",
                "--rows",
                "1000",
                "--accounts",
                "100",
            ],
        ]
        for command in commands:
            start = perf_counter()
            run = subprocess.run(command, cwd=checkout, capture_output=True, text=True, timeout=240)
            record = {
                "command": " ".join(command),
                "exit_code": run.returncode,
                "seconds": round(perf_counter() - start, 2),
                "output_tail": (run.stdout + run.stderr)[-4000:],
            }
            result["checks"].append(record)
            print(record["command"], "PASS" if run.returncode == 0 else "FAIL", flush=True)
            if run.returncode:
                print(record["output_tail"])
                break
        result["passed"] = len(result["checks"]) == len(commands) and all(
            c["exit_code"] == 0 for c in result["checks"]
        )
    (root / "docs" / "clean_checkout.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
