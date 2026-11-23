from pathlib import Path
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from ragforge.infrastructure.database import SessionFactory
from ragforge.main import create_app
from ragforge.models.document import Document
from ragforge.models.ingestion_job import IngestionJob
from ragforge.models.user import User
from ragforge.storage.factory import get_storage
from ragforge.storage.local import LocalFileStorage


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pdf_upload_is_private(
    tmp_path: Path,
) -> None:
    app = create_app()

    # Use temporary storage, not the real upload directory.
    storage = LocalFileStorage(tmp_path / "uploads")
    app.dependency_overrides[get_storage] = lambda: storage

    user_ids: list[UUID] = []
    document_id: UUID | None = None
    job_id: UUID | None = None

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            tokens: list[str] = []

            # 1. Register and log in as two users.
            for _ in range(2):
                email = f"upload-test-{uuid4().hex}@example.com"
                password = "TestPassword123!Secure"

                registered = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": email,
                        "password": password,
                    },
                )

                assert registered.status_code == 201, registered.text

                user_ids.append(UUID(registered.json()["data"]["id"]))

                logged_in = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": email,
                        "password": password,
                    },
                )

                assert logged_in.status_code == 200, logged_in.text

                tokens.append(logged_in.json()["data"]["access_token"])

            headers_a = {"Authorization": f"Bearer {tokens[0]}"}
            headers_b = {"Authorization": f"Bearer {tokens[1]}"}

            # 2. Upload a small test PDF as User A.
            # The upload route validates the PDF signature;
            # it does not parse the PDF during upload.
            pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"

            uploaded = await client.post(
                "/api/v1/uploads/pdf",
                headers=headers_a,
                files={
                    "file": (
                        "test-policy.pdf",
                        pdf_bytes,
                        "application/pdf",
                    )
                },
            )

            assert uploaded.status_code == 202, uploaded.text

            data = uploaded.json()["data"]

            document_id = UUID(data["document_id"])
            job_id = UUID(data["job_id"])

            assert data["status"] == "pending"

            # 3. User A can retrieve their document.
            own_document = await client.get(
                f"/api/v1/documents/{document_id}",
                headers=headers_a,
            )

            assert own_document.status_code == 200
            assert own_document.json()["data"]["name"] == ("test-policy.pdf")

            # 4. User A can retrieve their ingestion job.
            own_job = await client.get(
                f"/api/v1/ingestion-jobs/{job_id}",
                headers=headers_a,
            )

            assert own_job.status_code == 200
            assert own_job.json()["data"]["document_id"] == str(document_id)

            # 5. User B cannot access User A's document.
            other_document = await client.get(
                f"/api/v1/documents/{document_id}",
                headers=headers_b,
            )

            assert other_document.status_code == 404

            # 6. User B cannot access User A's job.
            other_job = await client.get(
                f"/api/v1/ingestion-jobs/{job_id}",
                headers=headers_b,
            )

            assert other_job.status_code == 404

            # 7. User B cannot see User A's document in lists.
            other_list = await client.get(
                "/api/v1/documents",
                headers=headers_b,
            )

            assert other_list.status_code == 200

            other_ids = {item["id"] for item in other_list.json()["data"]}

            assert str(document_id) not in other_ids

            # 8. Unauthenticated access is rejected.
            anonymous = await client.get(f"/api/v1/documents/{document_id}")

            assert anonymous.status_code == 401

            # 9. Confirm the upload really wrote a file.
            stored_files = list((tmp_path / "uploads").glob("*.pdf"))

            assert len(stored_files) == 1
            assert stored_files[0].read_bytes() == pdf_bytes

    finally:
        # Clean up in FK-safe order.
        async with SessionFactory.begin() as session:
            if job_id is not None:
                await session.execute(
                    delete(IngestionJob).where(IngestionJob.id == job_id)
                )

            if document_id is not None:
                await session.execute(
                    delete(Document).where(Document.id == document_id)
                )

            if user_ids:
                await session.execute(delete(User).where(User.id.in_(user_ids)))

        app.dependency_overrides.clear()
