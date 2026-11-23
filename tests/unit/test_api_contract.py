from ragforge.main import app


def test_document_api_contract() -> None:
    paths = app.openapi()["paths"]

    # PDF upload is the only public document-creation operation.
    assert "post" in paths["/api/v1/uploads/pdf"]

    # Documents can be listed and retrieved.
    assert "get" in paths["/api/v1/documents"]
    assert "get" in paths["/api/v1/documents/{document_id}"]

    # Direct document creation must not be exposed.
    assert "post" not in paths["/api/v1/documents"]


def test_conversation_api_contract() -> None:
    paths = app.openapi()["paths"]

    assert "post" in paths["/api/v1/conversations/ask"]
    assert "get" in paths["/api/v1/conversations"]
    assert "get" in paths["/api/v1/conversations/{conversation_id}/messages"]
