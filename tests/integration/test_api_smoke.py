import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data

def test_api_metrics_endpoint():
    response = client.get("/api/v1/metrics", headers={"X-Monitoring-Token": "sellerflow-monitoring-operator-key"})
    assert response.status_code == 200
    data = response.json()
    assert "workspaces_count" in data
    assert "total_orders" in data

def test_workspaces_list_and_create_authenticated():
    # Register a new user
    email = f"smoke_user_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SmokePassword123!",
        "full_name": "Smoke Test User",
        "workspace_name": "Initial Smoke Workspace"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List workspaces
    response = client.get("/api/v1/workspaces", headers=headers)
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) >= 1
    assert any(w["name"] == "Initial Smoke Workspace" for w in workspaces)

    # Test creating new workspace
    create_res = client.post("/api/v1/workspaces", data={"name": "Test Integration Corp"}, headers=headers)
    assert create_res.status_code == 200
    ws_data = create_res.json()
    assert ws_data["name"] == "Test Integration Corp"
    assert ws_data["role"] == "owner"
    assert "id" in ws_data
