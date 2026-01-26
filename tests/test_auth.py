import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@example.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "teacher@example.com"
    assert data["role"] == "teacher"
    assert "id" in data


def test_register_duplicate_email(client: TestClient):
    """Test registration with duplicate email."""
    # First registration
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@example.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    
    # Duplicate registration
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@example.com",
            "password": "AnotherPassword123",
            "role": "teacher"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client: TestClient):
    """Test successful login."""
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@example.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "teacher@example.com",
            "password": "SecurePassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Test login with wrong password."""
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@example.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    
    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "teacher@example.com",
            "password": "WrongPassword123"
        }
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123"
        }
    )
    assert response.status_code == 401


def test_refresh_token(client: TestClient):
    """Test token refresh."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@example.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "teacher@example.com",
            "password": "SecurePassword123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
