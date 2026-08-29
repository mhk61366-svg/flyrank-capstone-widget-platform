import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_tenant_id
from contextlib import contextmanager

FAKE_TENANT_ID = "11111111-1111-1111-1111-111111111111"

def override_get_current_tenant_id():
    return FAKE_TENANT_ID

@pytest.fixture
def client():
    app.dependency_overrides[get_current_tenant_id] = override_get_current_tenant_id
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from app.services.rate_limit import limiter
    limiter.reset()
    yield

@pytest.fixture
def public_client():
    return TestClient(app)

@pytest.fixture
def widget_id(public_client):
    app.dependency_overrides[get_current_tenant_id] = lambda: FAKE_TENANT_ID
    resp = public_client.post("/widgets", json={"title": "Test widget"})
    app.dependency_overrides.clear()
    return resp.json()["id"]

@contextmanager
def as_tenant(tenant_id):
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()