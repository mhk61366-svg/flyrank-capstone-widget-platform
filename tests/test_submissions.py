import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_tenant_id

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