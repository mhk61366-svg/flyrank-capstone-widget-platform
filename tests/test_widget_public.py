from fastapi.testclient import TestClient
from app.main import app

public = TestClient(app)

def test_config_returns_cache_header_and_no_tenant_id(client, widget_id):
    resp = public.get(f"/widgets/{widget_id}/config")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "public, max-age=60"
    assert "tenant_id" not in resp.json()

def test_config_404_for_nonexistent_widget():
    resp = public.get("/widgets/00000000-0000-0000-0000-000000000000/config")
    assert resp.status_code == 404

def test_widget_js_served_with_immutable_cache_header():
    resp = public.get("/widget.js")
    assert resp.status_code == 200
    assert "immutable" in resp.headers["cache-control"]
    assert "document.currentScript" in resp.text