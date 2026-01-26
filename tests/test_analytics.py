import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_token(client: TestClient):
    """Get authentication token for testing."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "analytics_teacher@test.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "analytics_teacher@test.com",
            "password": "SecurePassword123"
        }
    )
    return response.json()["access_token"]


def test_dashboard_empty(client: TestClient, auth_token: str):
    """Test dashboard with no data."""
    response = client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert data["stats"]["total_materials"] == 0
    assert data["stats"]["total_quizzes"] == 0
    assert data["stats"]["total_student_results"] == 0
    assert data["stats"]["average_score"] == 0.0
    assert data["recent_activities"] == []


def test_knowledge_map_empty(client: TestClient, auth_token: str):
    """Test knowledge map with no data."""
    response = client.get(
        "/api/v1/analytics/knowledge-map",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "knowledge_map" in data
    assert data["knowledge_map"] == []


def test_analytics_unauthorized(client: TestClient):
    """Test analytics endpoints without authentication."""
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 403
    
    response = client.get("/api/v1/analytics/knowledge-map")
    assert response.status_code == 403
