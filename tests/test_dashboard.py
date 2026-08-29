import pytest
from fastapi.testclient import TestClient
from app.main import app 
from tests.conftest import as_tenant

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"

@pytest.fixture
def widget_and_submissions():
    with as_tenant(TENANT_A) as client:
        widget_id = client.post("/widgets", json={"title": "Dashboard test widget"}).json()["id"]

    public = TestClient(app)
    base_payload = {"widget_id": widget_id, "name": "Test", "email": "a@b.com", "age": 25, "gender": "f"}
    public.post("/submissions", json=base_payload)
    public.post("/submissions", json={**base_payload, "hp_field": "bot"})
    return widget_id

def test_submissions_list_returns_all_rows_for_owner(widget_and_submissions):
    with as_tenant(TENANT_A) as client:
        resp = client.get(f"/widgets/{widget_and_submissions}/submissions")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_stats_excludes_spam_from_stored_count(widget_and_submissions):
    with as_tenant(TENANT_A) as client:
        resp = client.get(f"/widgets/{widget_and_submissions}/stats")
    body = resp.json()
    assert body["total_stored"] == 1
    assert body["total_spam_blocked"] == 1

def test_dashboard_endpoints_require_auth(widget_and_submissions):
    unauthenticated = TestClient(app)  # no override active — genuinely unauthenticated now
    assert unauthenticated.get(f"/widgets/{widget_and_submissions}/submissions").status_code == 401
    assert unauthenticated.get(f"/widgets/{widget_and_submissions}/stats").status_code == 401

def test_dashboard_endpoints_reject_other_tenant(widget_and_submissions):
    with as_tenant(TENANT_B) as client:
        submissions_resp = client.get(f"/widgets/{widget_and_submissions}/submissions")
        stats_resp = client.get(f"/widgets/{widget_and_submissions}/stats")
    assert submissions_resp.status_code == 404
    assert stats_resp.status_code == 404

def test_stats_and_submissions_empty_for_widget_with_no_submissions():
    with as_tenant(TENANT_A) as client:
        widget_id = client.post("/widgets", json={"title": "Empty widget"}).json()["id"]
        submissions_resp = client.get(f"/widgets/{widget_id}/submissions")
        stats_resp = client.get(f"/widgets/{widget_id}/stats")
    assert submissions_resp.json() == []
    body = stats_resp.json()
    assert body["total_stored"] == 0
    assert body["by_day"] == []
    assert body["by_country"] == []

def test_stats_includes_geo_breakdown(monkeypatch):
    from app.services import geo_enrichment
    monkeypatch.setattr(geo_enrichment, "enrich", lambda ip: {"country": "Testland", "city": "Testville"})

    with as_tenant(TENANT_A) as client:
        widget_id = client.post("/widgets", json={"title": "Geo test widget"}).json()["id"]

    public = TestClient(app)
    public.post("/submissions", json={
        "widget_id": widget_id, "name": "Test", "email": "a@b.com", "age": 25, "gender": "f"
    })

    with as_tenant(TENANT_A) as client:
        resp = client.get(f"/widgets/{widget_id}/stats")
    body = resp.json()
    assert body["by_country"] == [{"country": "Testland", "count": 1}]
    assert len(body["by_day"]) == 1