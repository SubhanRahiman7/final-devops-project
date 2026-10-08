from sqlalchemy.orm import sessionmaker

from app import main
from app.seed import seed_demo_data


def create(client, **overrides):
    payload = {"subject": "Cannot log in", "priority": "high", **overrides}
    response = client.post("/api/tickets", json=payload)
    assert response.status_code == 201
    return response.json()


def test_root_and_health(client):
    assert client.get("/").json()["service"] == "helpdesk-backend"
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_ready_returns_503_when_database_is_down(client, monkeypatch):
    class Broken:
        def __enter__(self):
            raise RuntimeError("db down")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(main, "SessionLocal", Broken)
    assert client.get("/ready").status_code == 503


def test_crud_lifecycle(client):
    ticket = create(client)
    assert ticket["status"] == "open"

    assert client.get(f"/api/tickets/{ticket['id']}").json()["subject"] == "Cannot log in"

    updated = client.put(f"/api/tickets/{ticket['id']}", json={"status": "resolved"}).json()
    assert updated["status"] == "resolved"
    assert updated["subject"] == "Cannot log in"  # untouched fields are kept

    assert client.delete(f"/api/tickets/{ticket['id']}").status_code == 204
    assert client.get(f"/api/tickets/{ticket['id']}").status_code == 404


def test_missing_ticket_returns_404(client):
    assert client.get("/api/tickets/999").status_code == 404
    assert client.put("/api/tickets/999", json={"status": "resolved"}).status_code == 404
    assert client.delete("/api/tickets/999").status_code == 404


def test_validation_rejects_bad_input(client):
    assert client.post("/api/tickets", json={"subject": ""}).status_code == 422
    assert client.post("/api/tickets", json={"subject": "x", "status": "weird"}).status_code == 422
    assert client.post("/api/tickets", json={"subject": "x", "priority": "asap"}).status_code == 422


def test_list_and_filters(client):
    create(client, subject="a", priority="low")
    create(client, subject="b", status="resolved", priority="urgent")
    assert len(client.get("/api/tickets").json()) == 2
    resolved = client.get("/api/tickets", params={"status": "resolved"}).json()
    assert [t["subject"] for t in resolved] == ["b"]
    urgent = client.get("/api/tickets", params={"priority": "urgent"}).json()
    assert [t["subject"] for t in urgent] == ["b"]


def test_stats(client):
    assert client.get("/api/tickets/stats").json()["resolution_rate"] == 0.0
    create(client, status="resolved")
    create(client, status="open", priority="urgent", category="billing")
    stats = client.get("/api/tickets/stats").json()
    assert stats["total"] == 2
    assert stats["by_status"] == {"open": 1, "in_progress": 0, "resolved": 1}
    assert stats["by_category"]["billing"] == 1
    assert stats["open_urgent"] == 1
    assert stats["resolution_rate"] == 50.0


def test_metrics_endpoint(client):
    client.get("/api/tickets")
    assert "http_requests_total" in client.get("/metrics").text


def test_seed_runs_once(db_engine):
    session = sessionmaker(bind=db_engine)()
    assert seed_demo_data(session) > 0
    assert seed_demo_data(session) == 0
