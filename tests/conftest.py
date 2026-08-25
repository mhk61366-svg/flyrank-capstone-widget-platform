import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_tenant_id

FAKE_TENANT_ID = "11111111-1111-1111-1111-111111111111"

def override_get_current_tenant_id():
    return FAKE_TENANT_ID

@pytest.fixture
def client():
    app.dependency_overrides[get_current_tenant_id] = override_get_current_tenant_id
    yield TestClient(app)
    app.dependency_overrides.clear()

