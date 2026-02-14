import io
from fastapi.testclient import TestClient


def _register_and_login_teacher(client: TestClient) -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "share.teacher@test.com",
            "password": "SecurePassword123",
            "role": "teacher"
        }
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "share.teacher@test.com",
            "password": "SecurePassword123"
        }
    )
    return response.json()["access_token"]


def _register_and_login_student(client: TestClient) -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "share.student@test.com",
            "password": "StudentPass123",
            "role": "student"
        }
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "share.student@test.com",
            "password": "StudentPass123"
        }
    )
    return response.json()["access_token"]


def _create_material(client: TestClient, token: str) -> str:
    files = {"file": ("lesson.txt", io.BytesIO(b"lesson content"), "text/plain")}
    response = client.post(
        "/api/v1/materials/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 202
    return response.json()["id"]


def _create_material_share(client: TestClient, token: str, material_id: str) -> str:
    response = client.post(
        "/api/v1/share/create",
        json={
            "resourceId": material_id,
            "resourceType": "material",
            "viewOnly": True,
            "allowCopy": False,
            "password": None,
            "expiresAt": None
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    url = response.json()["url"]
    return url.rsplit("/", 1)[-1]


def test_create_material_share_and_get_public_payload(client: TestClient):
    token = _register_and_login_teacher(client)
    material_id = _create_material(client, token)
    short_code = _create_material_share(client, token, material_id)

    response = client.get(f"/api/v1/share/{short_code}")
    assert response.status_code == 200
    payload = response.json()

    assert payload["resourceType"] == "material"
    assert payload["materialId"] == material_id
    assert payload["acceptUploads"] is True


def test_assignment_upload_rejects_unsupported_file_type(client: TestClient):
    token = _register_and_login_teacher(client)
    material_id = _create_material(client, token)
    short_code = _create_material_share(client, token, material_id)

    files = {
        "file": ("malware.exe", io.BytesIO(b"not allowed"), "application/octet-stream")
    }
    response = client.post(
        f"/api/v1/share/{short_code}/upload",
        data={"studentName": "Alice"},
        files=files
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_assignment_upload_accepts_txt_file(client: TestClient):
    token = _register_and_login_teacher(client)
    material_id = _create_material(client, token)
    short_code = _create_material_share(client, token, material_id)

    files = {"file": ("answer.txt", io.BytesIO(b"my homework"), "text/plain")}
    response = client.post(
        f"/api/v1/share/{short_code}/upload",
        data={"studentName": "Alice"},
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["studentName"] == "Alice"
    assert "submissionId" in data


def test_share_create_forbidden_for_student(client: TestClient):
    token = _register_and_login_student(client)

    response = client.post(
        "/api/v1/share/create",
        json={
            "resourceId": "00000000-0000-0000-0000-000000000000",
            "resourceType": "material",
            "viewOnly": True,
            "allowCopy": False,
            "password": None,
            "expiresAt": None
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_assignment_upload_rejects_oversized_file(client: TestClient):
    token = _register_and_login_teacher(client)
    material_id = _create_material(client, token)
    short_code = _create_material_share(client, token, material_id)

    huge_content = b"a" * (11 * 1024 * 1024)
    files = {"file": ("huge.txt", io.BytesIO(huge_content), "text/plain")}
    response = client.post(
        f"/api/v1/share/{short_code}/upload",
        data={"studentName": "Alice"},
        files=files
    )

    assert response.status_code == 400
    assert "File is too large" in response.json()["detail"]


def test_share_code_is_alphanumeric(client: TestClient):
    token = _register_and_login_teacher(client)
    material_id = _create_material(client, token)
    short_code = _create_material_share(client, token, material_id)

    assert len(short_code) == 8
    assert short_code.isalnum()


def test_get_shared_resource_rejects_invalid_short_code_format(client: TestClient):
    response = client.get("/api/v1/share/invalid-code")
    assert response.status_code == 400
    assert "Invalid short code format" in response.json()["detail"]


def test_submit_shared_quiz_rejects_invalid_short_code_format(client: TestClient):
    response = client.post(
        "/api/v1/share/invalid-code/submit",
        json={"studentName": "Alice", "answers": {}}
    )
    assert response.status_code == 400
    assert "Invalid short code format" in response.json()["detail"]


def test_upload_assignment_rejects_invalid_short_code_format(client: TestClient):
    files = {"file": ("answer.txt", io.BytesIO(b"text"), "text/plain")}
    response = client.post(
        "/api/v1/share/invalid-code/upload",
        data={"studentName": "Alice"},
        files=files
    )
    assert response.status_code == 400
    assert "Invalid short code format" in response.json()["detail"]
