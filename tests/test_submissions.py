import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_tenant_id
from app.services.submission_service import safe_ip
from app.services.rate_limit import limiter
from app.services import geo_enrichment

FAKE_TENANT_ID = "11111111-1111-1111-1111-111111111111"

@pytest.fixture
def public_client():
    return TestClient(app)

@pytest.fixture
def widget_id(public_client):
    app.dependency_overrides[get_current_tenant_id] = lambda: FAKE_TENANT_ID
    resp = public_client.post("/widgets", json={"title": "Test widget"})
    app.dependency_overrides.clear()
    return resp.json()["id"]

def valid_payload(widget_id):
    return {"widget_id": widget_id, "name": "Test", "email": "emamartinez@gmail.com", "age": 35, "gender": "female"}

def test_normalize_ip_accepts_valid_ip():
    assert safe_ip("8.8.8.8") == "8.8.8.8"

def test_normalize_ip_rejects_garbage():
    assert safe_ip("testclient") is None
    assert safe_ip(None) is None
    
def test_valid_submission_stored(public_client, widget_id):
    resp = public_client.post("/submissions", json=valid_payload(widget_id))
    assert resp.status_code == 201
    assert resp.json()["status"] == "stored"

def test_missing_required_field_returns_422(public_client, widget_id):
    payload = valid_payload(widget_id)
    del payload["age"]
    resp = public_client.post("/submissions", json=payload)
    assert resp.status_code == 422

def test_invalid_email_returns_422(public_client, widget_id):
    payload = valid_payload(widget_id)
    payload["email"] = "not-an-email"
    resp = public_client.post("/submissions", json=payload)
    assert resp.status_code == 422

def test_oversized_message_returns_422(public_client, widget_id):
    payload = valid_payload(widget_id)
    payload["message"] = "x" * 5000
    resp = public_client.post("/submissions", json=payload)
    assert resp.status_code == 422

def test_cors_preflight_allows_configured_origin(public_client):
    resp = public_client.options(
        "/submissions",
        headers={"Origin": "http://localhost:5500", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5500"

def test_cors_preflight_rejects_disallowed_origin(public_client):
    resp = public_client.options(
        "/submissions",
        headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in resp.headers

def test_honeypot_filled_marks_rejected_spam(public_client, widget_id):
    payload = valid_payload(widget_id)
    payload["hp_field"] = "im a bot"
    resp = public_client.post("/submissions", json=payload)
    assert resp.status_code == 201
    assert resp.json()["status"] == "rejected_spam"

def test_rate_limit_returns_429_after_burst(public_client, widget_id):
    payload = valid_payload(widget_id)
    statuses = [public_client.post("/submissions", json=payload).status_code for _ in range(15)]
    assert 429 in statuses

def test_normal_request_succeeds_after_rate_limit_window(public_client, widget_id):
    payload = valid_payload(widget_id)
    for _ in range(15):
        public_client.post("/submissions", json=payload)
    limiter.reset()
    resp = public_client.post("/submissions", json=payload)
    assert resp.status_code == 201

def test_geo_enrichment_uses_first_provider_when_available(monkeypatch):
    monkeypatch.setattr(geo_enrichment, "try_ip_api", lambda ip: {"country": "Realland", "city": "Realville"})
    monkeypatch.setattr(geo_enrichment, "try_ipapi_co", lambda ip: (_ for _ in ()).throw(AssertionError("should not be called")))
    result = geo_enrichment.enrich("1.2.3.4")
    assert result == {"country": "Realland", "city": "Realville"}
    
def test_geo_enrichment_falls_back_to_second_provider(public_client, widget_id, monkeypatch):
    monkeypatch.setattr(geo_enrichment, "try_ip_api", lambda ip: None)
    monkeypatch.setattr(geo_enrichment, "try_ipapi_co", lambda ip: {"country": "Testland", "city": "Testville"})
    result = geo_enrichment.enrich("1.2.3.4")
    assert result == {"country": "Testland", "city": "Testville"}

def test_geo_enrichment_returns_none_when_both_providers_down(monkeypatch):
    monkeypatch.setattr(geo_enrichment, "try_ip_api", lambda ip: None)
    monkeypatch.setattr(geo_enrichment, "try_ipapi_co", lambda ip: None)
    result = geo_enrichment.enrich("1.2.3.4")
    assert result == {"country": None, "city": None}

def test_submission_succeeds_when_both_geo_providers_down(public_client, widget_id, monkeypatch):
    monkeypatch.setattr(geo_enrichment, "try_ip_api", lambda ip: None)
    monkeypatch.setattr(geo_enrichment, "try_ipapi_co", lambda ip: None)
    resp = public_client.post("/submissions", json=valid_payload(widget_id))
    assert resp.status_code == 201
    assert resp.json()["status"] == "stored"