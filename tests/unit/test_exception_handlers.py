from uuid import uuid4

from fastapi.testclient import TestClient

from ragforge.api.auth import CurrentUser, get_current_user
from ragforge.core.exceptions import DocumentNotFoundException
from ragforge.main import create_app


def _override_user() -> CurrentUser:
    return CurrentUser(id=uuid4())


def test_global_exception_handler() -> None:
    app = create_app()

    @app.get("/test-not-found")
    def test_route():
        raise DocumentNotFoundException()

    with TestClient(app) as client:
        response = client.get("/test-not-found")

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_validation_error_format() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = _override_user

    with TestClient(app) as client:
        response = client.get("/api/v1/documents/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
