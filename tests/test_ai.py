"""Tests for AI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


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


@pytest.fixture
def material_id(client: TestClient, auth_token: str, db_session):
    """Create a test material and return its ID."""
    from app.models.models import Material
    import uuid
    
    material = Material(
        id=uuid.uuid4(),
        user_id=db_session.query(Material).first().user_id if db_session.query(Material).first() else uuid.uuid4(),
        title="Test Material",
        raw_text="This is a sample educational text about Python programming. Python is a high-level programming language.",
        file_url="/uploads/test.pdf"
    )
    db_session.add(material)
    db_session.commit()
    
    return str(material.id)


def test_generate_summary_unauthorized(client: TestClient):
    """Test generate summary without authentication."""
    response = client.post(
        "/api/v1/ai/generate-summary",
        json={"material_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert response.status_code == 403


@patch('app.services.ai_service.ai_service.generate_summary')
def test_generate_summary_success(mock_generate, client: TestClient, auth_token: str, material_id: str):
    """Test successful summary generation."""
    mock_generate.return_value = AsyncMock(return_value={
        "is_educational": True,
        "summary": "Test summary",
        "glossary": {"Python": "A programming language"}
    })()
    
    response = client.post(
        "/api/v1/ai/generate-summary",
        json={"material_id": material_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "glossary" in data


def test_generate_summary_nonexistent_material(client: TestClient, auth_token: str):
    """Test summary generation for nonexistent material."""
    response = client.post(
        "/api/v1/ai/generate-summary",
        json={"material_id": "00000000-0000-0000-0000-000000000000"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


def test_generate_quiz_unauthorized(client: TestClient):
    """Test generate quiz without authentication."""
    response = client.post(
        "/api/v1/ai/generate-quiz",
        json={
            "material_id": "00000000-0000-0000-0000-000000000000",
            "num_questions": 5,
            "difficulty": "medium"
        }
    )
    assert response.status_code == 403


@patch('app.services.ai_service.ai_service.generate_quiz')
def test_generate_quiz_success(mock_generate, client: TestClient, auth_token: str, material_id: str):
    """Test successful quiz generation."""
    mock_generate.return_value = AsyncMock(return_value={
        "questions": [
            {
                "question": "What is Python?",
                "options": ["A snake", "A programming language", "A tool", "A framework"],
                "correct_answer": "A programming language",
                "explanation": "Python is a high-level programming language."
            }
        ]
    })()
    
    response = client.post(
        "/api/v1/ai/generate-quiz",
        json={
            "material_id": material_id,
            "num_questions": 1,
            "difficulty": "medium"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) > 0


def test_generate_quiz_invalid_difficulty(client: TestClient, auth_token: str, material_id: str):
    """Test quiz generation with invalid difficulty."""
    response = client.post(
        "/api/v1/ai/generate-quiz",
        json={
            "material_id": material_id,
            "num_questions": 5,
            "difficulty": "invalid"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422


def test_generate_quiz_invalid_num_questions(client: TestClient, auth_token: str, material_id: str):
    """Test quiz generation with invalid number of questions."""
    response = client.post(
        "/api/v1/ai/generate-quiz",
        json={
            "material_id": material_id,
            "num_questions": 0,
            "difficulty": "medium"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422
