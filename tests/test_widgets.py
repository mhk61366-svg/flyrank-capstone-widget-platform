from fastapi.testclient import TestClient
from app.main import app

unauthenticated_client = TestClient(app)

def test_create_widget_requires_auth():
    response = unauthenticated_client.post("/widgets", json={"title": "x"})
    assert response.status_code == 401

def test_create_and_get_widget(client):
    create_resp = client.post("/widgets", json={"title": "My signup form","description":"Enter credentials to sign up"})
    assert create_resp.status_code == 201
    widget_id = create_resp.json()["id"]
    get_resp = client.get(f"/widgets/{widget_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "My signup form"

def test_get_nonexistent_widget_returns_404(client):
    response = client.get("/widgets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
FAKE_TENANT_B = "22222222-2222-2222-2222-222222222222"

def test_tenant_isolation_on_get_update_delete(client, monkeypatch):
    from app.auth import get_current_tenant_id
    create_resp = client.post("/widgets", json={"title": "Tenant A's widget"})
    widget_id = create_resp.json()["id"]

    def override_tenant_b():
        return FAKE_TENANT_B
    app.dependency_overrides[get_current_tenant_id] = override_tenant_b
    tenant_b_client = TestClient(app)

    assert tenant_b_client.get(f"/widgets/{widget_id}").status_code == 404
    assert tenant_b_client.patch(f"/widgets/{widget_id}", json={"title": "Hijacked"}).status_code == 404
    assert tenant_b_client.delete(f"/widgets/{widget_id}").status_code == 404

def test_update_widget(client):
    create_resp = client.post("/widgets", json={"title": "Original"})
    widget_id = create_resp.json()["id"]

    update_resp = client.patch(f"/widgets/{widget_id}", json={"title": "Updated"})
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated"

def test_delete_widget(client):
    create_resp = client.post("/widgets", json={"title": "To delete"})
    widget_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/widgets/{widget_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/widgets/{widget_id}")
    assert get_resp.status_code == 404