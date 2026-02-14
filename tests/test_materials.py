import pytest
import io
from fastapi.testclient import TestClient


@pytest.fixture
def auth_token(client: TestClient):
    """Get authentication token for testing."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@test.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "teacher@test.com",
            "password": "SecurePassword123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def student_token(client: TestClient):
    """Get authentication token for student."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_materials@test.com",
            "password": "StudentPass123",
            "role": "student"
        }
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student_materials@test.com",
            "password": "StudentPass123"
        }
    )
    return response.json()["access_token"]


def test_upload_material_unauthorized(client: TestClient):
    """Test material upload without authentication."""
    # Create a fake PDF file
    file_content = b"Fake PDF content"
    files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    
    response = client.post("/api/v1/materials/upload", files=files)
    assert response.status_code == 403  # Forbidden without auth


def test_list_materials_empty(client: TestClient, auth_token: str):
    """Test listing materials when none exist."""
    response = client.get(
        "/api/v1/materials/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_nonexistent_material(client: TestClient, auth_token: str):
    """Test getting a material that doesn't exist."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/api/v1/materials/{fake_uuid}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


def test_materials_forbidden_for_student(client: TestClient, student_token: str):
    """Student should not access teacher materials endpoints."""
    response = client.get(
        "/api/v1/materials/",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403
