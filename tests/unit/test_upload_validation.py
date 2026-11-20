from fastapi.testclient import TestClient

from ragforge.main import create_app


def test_reject_non_pdf_extension() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/uploads/pdf",
            files={"file": ("test.txt", b"Hello", "text/plain")},
        )

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_reject_invalid_pdf_signature() -> None:
    app = create_app()

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
