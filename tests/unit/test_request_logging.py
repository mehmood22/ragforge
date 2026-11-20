from fastapi.testclient import TestClient

from ragforge.main import create_app


def test_request_has_correlation_id() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) == 32
