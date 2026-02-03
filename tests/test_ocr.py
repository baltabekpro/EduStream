"""Tests for OCR endpoints."""
import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def auth_token(client: TestClient):
    """Get authentication token for testing."""
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


def test_extract_text_unauthorized(client: TestClient):
    """Test OCR extraction without authentication."""
    file_content = b"Fake image content"
    files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    response = client.post("/api/v1/ocr/extract", files=files)
    assert response.status_code == 403


@patch('app.services.ocr_service.ocr_service.extract_text_from_image')
def test_extract_text_success(mock_extract, client: TestClient, auth_token: str):
    """Test successful OCR text extraction."""
    mock_extract.return_value = MagicMock(return_value="Extracted text from image")
    
    file_content = b"Fake image content"
    files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    response = client.post(
        "/api/v1/ocr/extract",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 0


def test_extract_text_invalid_file_type(client: TestClient, auth_token: str):
    """Test OCR extraction with invalid file type."""
    file_content = b"Not an image"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    
    response = client.post(
        "/api/v1/ocr/extract",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400


@patch('app.services.ocr_service.ocr_service.extract_text_from_image')
def test_extract_text_empty_result(mock_extract, client: TestClient, auth_token: str):
    """Test OCR extraction with no text found."""
    mock_extract.return_value = MagicMock(return_value="")
    
    file_content = b"Fake image content"
    files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    response = client.post(
        "/api/v1/ocr/extract",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == ""


def test_extract_text_large_file(client: TestClient, auth_token: str):
    """Test OCR extraction with large file."""
    # Create a file larger than the limit (if there is one)
    file_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    response = client.post(
        "/api/v1/ocr/extract",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Should either succeed or return 413 (Payload Too Large)
    assert response.status_code in [200, 413]


@patch('app.services.ocr_service.ocr_service.extract_text_from_image')
def test_extract_text_multiple_files_sequential(mock_extract, client: TestClient, auth_token: str):
    """Test multiple OCR extractions sequentially."""
    mock_extract.return_value = MagicMock(return_value="Extracted text")
    
    for i in range(3):
        file_content = f"Image {i}".encode()
        files = {"file": (f"test{i}.jpg", io.BytesIO(file_content), "image/jpeg")}
        
        response = client.post(
            "/api/v1/ocr/extract",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
