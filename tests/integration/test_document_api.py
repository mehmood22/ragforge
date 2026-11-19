from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from ragforge.infrastructure.database import SessionFactory
from ragforge.main import create_app
from ragforge.models.document import Document


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_get_document() -> None:
    app = create_app()

    transport = ASGITransport(app=app)

    document_id = None

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        try:
            response = await client.post(
                "/api/v1/documents",
                json={
                    "name": f"Test Document {uuid4()}",
                    "source_type": "pdf",
                    "source_uri": None,
                },
            )

            assert response.status_code == 201

            body = response.json()
            assert body["success"] is True

            document_data = body["data"]
            document_id = document_data["id"]

            assert document_data["status"] == "pending"
            assert document_data["chunk_count"] == 0

            get_response = await client.get(f"/api/v1/documents/{document_id}")

            assert get_response.status_code == 200
            get_body = get_response.json()
            assert get_body["success"] is True
            assert get_body["data"]["id"] == document_id

        finally:
            if document_id is not None:
                async with SessionFactory.begin() as session:
                    await session.execute(
                        delete(Document).where(Document.id == UUID(document_id))
                    )