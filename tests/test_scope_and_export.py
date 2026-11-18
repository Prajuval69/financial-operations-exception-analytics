def test_transaction_dimensions_dates_and_lookup(client):
    from collections import Counter

    rows = client.get("/api/v1/transactions?page_size=500").json()["items"]
    counts = Counter(r["transaction_id"] for r in rows)
    row = next(
        r
        for r in rows
        if r["transaction_id"]
        and counts[r["transaction_id"]] == 1
        and r["transaction_day"]
        and r["team_id"].startswith("TEAM")
        and r["source_system_id"].startswith("SRC")
    )
    params = {
        "team": row["team_id"],
        "source_system": row["source_system_id"],
        "status": row["status"],
    }
    result = client.get("/api/v1/transactions", params=params).json()
    assert result["total"] > 0
    assert all(
        r["team_id"] == row["team_id"]
        and r["source_system_id"] == row["source_system_id"]
        and r["status"] == row["status"]
        for r in result["items"]
    )
    day = row["transaction_day"]
    dated = client.get("/api/v1/transactions", params={"date_from": day, "date_to": day}).json()
    assert all(r["transaction_day"] == day for r in dated["items"])
    assert client.get(f"/api/v1/transactions/{row['transaction_id']}").status_code == 200


def test_workflow_filters_risk_closure_and_audit(client):
    action = client.post(
        "/api/v1/actions",
        json={
            "title": "Control review",
            "owner": "Mapping Desk",
            "due_date": "2026-10-01",
            "priority": "P1",
        },
    ).json()
    assert client.get("/api/v1/actions?owner=Mapping%20Desk&priority=P1").json()["total"] == 1
    risk = client.post(
        "/api/v1/risks",
        json={
            "title": "Control exposure",
            "owner": "Mapping Desk",
            "due_date": "2026-10-01",
            "probability": 5,
            "impact": 4,
            "action_id": action["action_id"],
        },
    ).json()
    assert (
        client.patch(f"/api/v1/risks/{risk['risk_id']}", json={"status": "Closed"}).status_code
        == 200
    )
    assert client.get("/api/v1/risks?status=Closed&owner=Mapping%20Desk").json()["total"] == 1
    assert client.get("/api/v1/kpis/summary").json()["values"]["KPI050"] == 0
    assert client.get("/api/v1/audit").json()["total"] >= 3


def test_html_escapes_workflow_content(session, policy, tmp_path):
    from app.api.schemas import RiskCreate
    from app.reports.service import generate_executive
    from app.services.analytics import build_analytics
    from app.services.workflow import create_risk

    create_risk(
        session,
        RiskCreate(
            title="<script>alert('x')</script>",
            owner="Desk",
            due_date="2026-10-01",
            probability=2,
            impact=3,
        ),
    )
    content = generate_executive(build_analytics(session, policy), tmp_path).read_text(
        encoding="utf-8"
    )
    assert "<script>alert('x')</script>" not in content and "&lt;script&gt;" in content
