"""Tests for user management endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def teacher_token(client: TestClient):
    """Get authentication token for teacher."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@test.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    
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
            "email": "student@test.com",
            "password": "StudentPass123",
            "role": "student"
        }
    )
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@test.com",
            "password": "StudentPass123"
        }
    )
    return response.json()["access_token"]


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without authentication."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 403


def test_get_current_user_teacher(client: TestClient, teacher_token: str):
    """Test getting current user info as teacher."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "teacher@test.com"
    assert data["role"] == "teacher"
    assert "id" in data


def test_get_current_user_student(client: TestClient, student_token: str):
    """Test getting current user info as student."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "student@test.com"
    assert data["role"] == "student"


def test_update_profile_teacher(client: TestClient, teacher_token: str):
    """Test updating teacher profile."""
    response = client.put(
        "/api/v1/users/me",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Math teacher"
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["bio"] == "Math teacher"


def test_update_profile_student(client: TestClient, student_token: str):
    """Test updating student profile."""
    response = client.put(
        "/api/v1/users/me",
        json={
            "first_name": "Jane",
            "last_name": "Smith"
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"


def test_update_profile_unauthorized(client: TestClient):
    """Test updating profile without authentication."""
    response = client.put(
        "/api/v1/users/me",
        json={"first_name": "John"}
    )
    assert response.status_code == 403


def test_change_password_success(client: TestClient, teacher_token: str):
    """Test successful password change."""
    response = client.post(
        "/api/v1/users/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "NewSecurePassword456"
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    
    # Try login with new password
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "teacher@test.com",
            "password": "NewSecurePassword456"
        }
    )
    assert login_response.status_code == 200


def test_change_password_wrong_current(client: TestClient, teacher_token: str):
    """Test password change with wrong current password."""
    response = client.post(
        "/api/v1/users/change-password",
        json={
            "current_password": "WrongPassword123",
            "new_password": "NewSecurePassword456"
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 400


def test_change_password_weak_new(client: TestClient, teacher_token: str):
    """Test password change with weak new password."""
    response = client.post(
        "/api/v1/users/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "123"
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 422


def test_delete_account(client: TestClient, teacher_token: str):
    """Test account deletion."""
    response = client.delete(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    
    # Try to access with old token (should fail)
    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert me_response.status_code in [401, 404]
