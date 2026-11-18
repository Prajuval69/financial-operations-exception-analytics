from app.cli import main


def test_cli_end_to_end(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FINOPS_DATABASE_URL", f"sqlite:///{(tmp_path / 'cli.db').as_posix()}")
    monkeypatch.setenv("FINOPS_OUTPUT_DIR", str(tmp_path / "reports"))
    assert main(["init-db"]) == 0
    assert (
        main(["demo", "--rows", "300", "--accounts", "30", "--export-dir", str(tmp_path / "raw")])
        == 0
    )
    assert len(list((tmp_path / "reports").glob("*.xlsx"))) == 1
    assert main(["validate"]) == 0
    assert main(["kpis"]) == 0
    assert main(["seed", "--rows", "10"]) == 1
    assert main(["reset-db", "--yes"]) == 0
    assert (
        main(
            [
                "ingest",
                str(tmp_path / "raw" / "transactions.csv"),
                "--accounts",
                str(tmp_path / "raw" / "accounts.csv"),
                "--synthetic",
                "--as-of",
                "2026-09-30T18:00:00",
            ]
        )
        == 0
    )
    assert main(["validate"]) == 0
    assert main(["report", "all"]) == 0
    output = capsys.readouterr().out
    assert '"new_exceptions": 0' in output


def test_cli_invalid_asof(tmp_path, monkeypatch):
    monkeypatch.setenv("FINOPS_DATABASE_URL", f"sqlite:///{(tmp_path / 'bad.db').as_posix()}")
    assert main(["seed", "--rows", "5", "--as-of", "invalid"]) == 1
