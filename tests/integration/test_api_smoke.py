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
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "workspaces_count" in data
    assert "total_orders" in data

def test_workspaces_list_and_create():
    response = client.get("/api/v1/workspaces")
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) > 0

    # Test creating new workspace
    create_res = client.post("/api/v1/workspaces", data={"name": "Test Integration Corp"})
    assert create_res.status_code == 200
    ws_data = create_res.json()
    assert ws_data["name"] == "Test Integration Corp"
    assert "id" in ws_data
