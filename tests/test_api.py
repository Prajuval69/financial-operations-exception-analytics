from sqlalchemy import select

from app.db.models import Transaction
from app.db.session import session_scope


def test_health_pagination_and_filters(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/openapi.json").status_code == 200
    first = client.get("/api/v1/transactions", params={"page_size": 10}).json()
    second = client.get("/api/v1/transactions", params={"page_size": 10, "page": 2}).json()
    assert first["total"] == 250 and len(first["items"]) == 10
    assert {r["id"] for r in first["items"]}.isdisjoint({r["id"] for r in second["items"]})
    unit = first["items"][0]["business_unit_id"]
    subset = client.get("/api/v1/transactions", params={"business_unit": unit}).json()
    assert all(r["business_unit_id"] == unit for r in subset["items"])
    assert client.get("/api/v1/transactions?page=0").status_code == 422
    assert client.get("/api/v1/transactions?page_size=10000").status_code == 422
    assert (
        client.get("/api/v1/transactions?date_from=2026-10-01&date_to=2026-09-01").status_code
        == 422
    )


def test_transaction_lookup_and_duplicate_ambiguity(client, engine):
    assert client.get("/api/v1/transactions/DOES_NOT_EXIST").status_code == 404
    with session_scope(engine) as session:
        row = session.scalar(select(Transaction).where(Transaction.transaction_id.is_not(None)))
        session.scalar(
            select(Transaction).where(Transaction.id != row.id)
        ).transaction_id = row.transaction_id
        tx_id = row.transaction_id
    assert client.get(f"/api/v1/transactions/{tx_id}").status_code == 409


def test_validation_and_kpi_endpoints(client):
    assert client.post("/api/v1/validation/run", json={}).json()["new_exceptions"] == 0
    assert client.post("/api/v1/validation/run", json={"as_of": "bad"}).status_code == 422
    for route in [
        "validation/summary",
        "kpis/summary",
        "kpis/trends",
        "kpis/exceptions",
        "kpis/teams",
        "references",
        "audit",
    ]:
        assert client.get(f"/api/v1/{route}").status_code == 200
    kpis = client.get("/api/v1/kpis/summary").json()
    assert kpis["values"]["KPI001"] == 250
    assert (
        client.get("/api/v1/kpis/summary?business_unit=MISSING").json()["values"]["KPI010"] is None
    )


def test_exception_updates_and_rollback(client):
    item = client.get("/api/v1/exceptions").json()["items"][0]
    url = f"/api/v1/exceptions/{item['exception_id']}"
    assert client.get(url).status_code == 200
    assert client.patch(url, json={"status": "Closed"}).status_code == 409
    assert client.get(url).json()["status"] == "Detected"
    assert client.patch(url, json={"owner": None}).status_code == 422
    assert (
        client.patch(url, json={"status": "Assigned", "owner": "Control Desk"}).status_code == 200
    )
    assert client.patch(url, json={"status": "INVALID"}).status_code == 422
    assert client.patch(url, json={"severity": "Low"}).status_code == 422
    assert client.get("/api/v1/exceptions/999999").status_code == 404


def test_action_and_risk_crud_invalid_inputs(client):
    action = {
        "title": "Verify reference mapping",
        "owner": "Desk",
        "due_date": "2026-10-01T12:00:00",
    }
    created = client.post("/api/v1/actions", json=action)
    assert created.status_code == 201
    action_id = created.json()["action_id"]
    assert client.patch(f"/api/v1/actions/{action_id}", json={"status": "Completed"}).json()[
        "completed_at"
    ]
    assert client.get("/api/v1/actions?status=Completed").json()["total"] == 1
    assert client.post("/api/v1/actions", json=action | {"exception_id": 99999}).status_code == 404
    assert client.post("/api/v1/actions", json=action | {"owner": " "}).status_code == 422
    risk = {
        "title": "Reference control risk",
        "owner": "Desk",
        "due_date": "2026-10-01",
        "probability": 3,
        "impact": 4,
        "action_id": action_id,
    }
    created = client.post("/api/v1/risks", json=risk)
    assert created.status_code == 201 and created.json()["risk_score"] == 12
    assert (
        client.patch(f"/api/v1/risks/{created.json()['risk_id']}", json={"impact": 5}).json()[
            "risk_score"
        ]
        == 15
    )
    assert client.post("/api/v1/risks", json=risk | {"probability": 6}).status_code == 422
    assert client.post("/api/v1/risks", json=risk | {"probability": 2.5}).status_code == 422
    assert client.get("/api/v1/risks").json()["total"] == 1
    assert client.patch("/api/v1/actions/999999", json={"status": "Completed"}).status_code == 404
