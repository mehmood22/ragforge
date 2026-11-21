from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ragforge.services.upload_service import UploadService
from ragforge.storage.base import StoredFile


@pytest.mark.asyncio
async def test_upload_creates_document_and_job() -> None:
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    def set_ids() -> None:
        for obj in [call.args[0] for call in session.add.call_args_list]:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    session.flush.side_effect = set_ids

    storage = AsyncMock()
    storage.upload.return_value = StoredFile(
        key="test.pdf",
        size=8,
    )

    service = UploadService(
        session=session,
        storage=storage,
    )

    result = await service.submit_pdf(
        filename="test.pdf",
        content=b"%PDF-test",
    )

    assert result.document_id is not None
    assert result.job_id is not None

    assert session.add.call_count == 2
    assert session.flush.await_count == 2
    session.commit.assert_awaited_once()
    storage.upload.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_cleans_file_on_database_failure() -> None:
    session = MagicMock()
    session.flush = AsyncMock(side_effect=RuntimeError("Database error"))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    storage = AsyncMock()
    storage.upload.return_value = StoredFile(
        key="failed.pdf",
        size=8,
    )

    service = UploadService(
        session=session,
        storage=storage,
    )

    with pytest.raises(RuntimeError):
        await service.submit_pdf(
            filename="failed.pdf",
            content=b"%PDF-test",
        )

    session.rollback.assert_awaited_once()
    storage.delete.assert_awaited_once_with("failed.pdf")
