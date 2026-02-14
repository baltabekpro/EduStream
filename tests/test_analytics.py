import pytest
from fastapi.testclient import TestClient
from app.models.models import User, Course, Material, Quiz, StudentResult, MaterialStatus


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


def test_analytics_forbidden_for_student(client: TestClient):
    """Student should not access teacher analytics endpoints."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "analytics_student@test.com",
            "password": "StudentPass123",
            "role": "student"
        }
    )
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "analytics_student@test.com",
            "password": "StudentPass123"
        }
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_student_journal_and_comment(client: TestClient, db_session, auth_token: str):
    teacher = db_session.query(User).filter(User.email == "analytics_teacher@test.com").first()
    assert teacher is not None

    course = Course(user_id=teacher.id, title="Алгебра")
    db_session.add(course)
    db_session.flush()

    material = Material(
        user_id=teacher.id,
        title="Квадратные уравнения",
        content="Тестовый контент",
        status=MaterialStatus.READY,
        course_id=str(course.id)
    )
    db_session.add(material)
    db_session.flush()

    quiz = Quiz(
        material_id=material.id,
        title="Контрольная",
        questions=[
            {"id": "q1", "text": "2+2", "type": "mcq", "options": ["3", "4"], "correctAnswer": "4"}
        ]
    )
    db_session.add(quiz)
    db_session.flush()

    db_session.add_all([
        StudentResult(user_id=teacher.id, student_identifier="Айгерим", quiz_id=quiz.id, score=90, weak_topics=["Дроби"]),
        StudentResult(user_id=teacher.id, student_identifier="Айгерим", quiz_id=quiz.id, score=88, weak_topics=["Проценты"]),
        StudentResult(user_id=teacher.id, student_identifier="Айгерим", quiz_id=quiz.id, score=92, weak_topics=[]),
        StudentResult(user_id=teacher.id, student_identifier="Нурдаулет", quiz_id=quiz.id, score=64, weak_topics=["Уравнения"]),
    ])
    db_session.commit()

    response = client.get(
        f"/api/v1/analytics/student-journal?courseId={course.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["totalStudents"] == 2
    assert payload["regularStudents"] == 1
    assert len(payload["students"]) == 2

    comment_response = client.patch(
        "/api/v1/analytics/student-journal/comment",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "courseId": str(course.id),
            "studentName": "Айгерим",
            "comment": "Стабильный прогресс, продолжай в том же темпе"
        }
    )
    assert comment_response.status_code == 200

    updated = client.get(
        f"/api/v1/analytics/student-journal?courseId={course.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert updated.status_code == 200
    updated_payload = updated.json()
    student = next(item for item in updated_payload["students"] if item["studentName"] == "Айгерим")
    assert "Стабильный прогресс" in student["teacherComment"]


def test_quiz_results_filtered_by_course(client: TestClient, db_session, auth_token: str):
    teacher = db_session.query(User).filter(User.email == "analytics_teacher@test.com").first()
    assert teacher is not None

    course_a = Course(user_id=teacher.id, title="Физика")
    course_b = Course(user_id=teacher.id, title="История")
    db_session.add_all([course_a, course_b])
    db_session.flush()

    material_a = Material(user_id=teacher.id, title="Силы", content="x", status=MaterialStatus.READY, course_id=str(course_a.id))
    material_b = Material(user_id=teacher.id, title="Рим", content="x", status=MaterialStatus.READY, course_id=str(course_b.id))
    db_session.add_all([material_a, material_b])
    db_session.flush()

    quiz_a = Quiz(material_id=material_a.id, title="Физика тест", questions=[])
    quiz_b = Quiz(material_id=material_b.id, title="История тест", questions=[])
    db_session.add_all([quiz_a, quiz_b])
    db_session.flush()

    db_session.add_all([
        StudentResult(user_id=teacher.id, student_identifier="A", quiz_id=quiz_a.id, score=80, weak_topics=[]),
        StudentResult(user_id=teacher.id, student_identifier="B", quiz_id=quiz_b.id, score=55, weak_topics=[]),
    ])
    db_session.commit()

    response = client.get(
        f"/api/v1/share/quiz-results?courseId={course_a.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["materialTitle"] == "Силы"
