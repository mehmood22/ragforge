from uuid import uuid4

from fastapi.testclient import TestClient

from ragforge.api.auth import CurrentUser, get_current_user
from ragforge.main import create_app


def _override_user() -> CurrentUser:
    return CurrentUser(id=uuid4())


def test_reject_non_pdf_extension() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = _override_user

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/uploads/pdf",
            files={"file": ("test.txt", b"Hello", "text/plain")},
        )

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_reject_invalid_pdf_signature() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = _override_user

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/uploads/pdf",
            files={
                "file": (
                    "fake.pdf",
                    b"This is not a real PDF",
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
