from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

from app.db.session import session_scope
from app.main import create_app
from app.reports.service import generate_excel, generate_executive, safe_cell
from app.services.analytics import build_analytics
from app.services.generator import GeneratorConfig
from app.services.ingestion import seed_dataset
from app.services.validation import run_validation
from app.services.workflow import seed_demo_workflow

SHEETS = {
    "Executive Summary",
    "KPI Summary",
    "Data Quality",
    "Exceptions",
    "Operational Performance",
    "Actions",
    "Risks",
    "Raw Processed Data Sample",
    "Data Dictionary",
    "Methodology",
}


def test_excel_html_reports(session, policy, tmp_path):
    seed_dataset(session, GeneratorConfig(rows=500, accounts=50))
    run_validation(session, policy)
    seed_demo_workflow(session)
    result = build_analytics(session, policy)
    workbook_path = generate_excel(result, tmp_path)
    executive_path = generate_executive(result, tmp_path)
    workbook = load_workbook(workbook_path)
    assert set(workbook.sheetnames) == SHEETS
    assert all(workbook[name].freeze_panes == "A2" for name in SHEETS)
    assert workbook["KPI Summary"]["E2"].value == 500
    assert workbook["KPI Summary"]["E5"].number_format == "0.00%"
    assert workbook["Exceptions"].max_row == len(result["bundle"]["exceptions"]) + 1
    from app.services.dictionary import data_dictionary

    assert workbook["Data Dictionary"].max_row == len(data_dictionary()) + 1
    content = executive_path.read_text(encoding="utf-8")
    for section in [
        "Executive Summary",
        "Operational KPI Scorecard",
        "Data Quality Assessment",
        "Exception Analysis",
        "Operational Trends",
        "Risks and Actions",
        "Key Findings",
        "Recommendations",
        "Methodology",
        "Limitations",
    ]:
        assert section in content
    assert "plotly.js" in content and '<script src="https://' not in content
    assert "500 transaction rows" in content
    assert not list(tmp_path.glob(".finops-*"))


def test_empty_reports_and_formula_injection(session, policy, tmp_path):
    analytics = build_analytics(session, policy)
    assert generate_excel(analytics, tmp_path).exists()
    assert "N/A" in generate_executive(analytics, tmp_path).read_text(encoding="utf-8")
    for text in ['=HYPERLINK("bad")', "+SUM(A1)", " @BAD", "-125"]:
        assert safe_cell(text).startswith("'")


def test_api_report_downloads(engine, policy, tmp_path):
    policy.output_dir = tmp_path
    with session_scope(engine) as session:
        seed_dataset(session, GeneratorConfig(rows=100, accounts=10))
        run_validation(session, policy)
    with TestClient(create_app(policy, engine)) as client:
        for kind in ["excel", "executive"]:
            response = client.post(f"/api/v1/reports/{kind}?business_unit=BU01")
            assert response.status_code == 200
            assert "attachment" in response.headers["content-disposition"]
            assert len(response.content) > 5000
        assert client.post("/api/v1/reports/unknown").status_code == 422


@pytest.mark.parametrize("seeded", [False, True])
def test_all_dashboard_views(tmp_path, monkeypatch, seeded):
    monkeypatch.setenv("FINOPS_DATABASE_URL", f"sqlite:///{(tmp_path / 'dashboard.db').as_posix()}")
    monkeypatch.setenv("FINOPS_OUTPUT_DIR", str(tmp_path))
    from app.core.config import get_settings
    from app.db.session import init_db, make_engine
    from dashboard.app import PAGES, database_engine

    database_engine.clear()
    policy = get_settings()
    engine = make_engine(policy)
    init_db(engine)
    if seeded:
        with session_scope(engine) as session:
            seed_dataset(session, GeneratorConfig(rows=300, accounts=30))
            run_validation(session, policy)
            seed_demo_workflow(session)
    test = AppTest.from_file(str(Path("dashboard/app.py").resolve()), default_timeout=30).run()
    assert not test.exception and not test.error
    for page in PAGES:
        test.sidebar.radio[0].set_value(page).run()
        assert not test.exception and not test.error, page
        assert test.title[0].value == page
    engine.dispose()
    database_engine.clear()
