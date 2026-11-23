from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from ragforge.api.routes.ingestion_jobs import (
    get_ingestion_job,
)
from ragforge.core.exceptions import NotFoundException


@pytest.mark.asyncio
async def test_job_endpoint_checks_ownership() -> None:
    job_id = uuid4()
    user_id = uuid4()

    session = AsyncMock()
    current_user = type(
        "CurrentUser",
        (),
        {"id": user_id},
    )()

    with patch(
        "ragforge.api.routes.ingestion_jobs.IngestionJobRepository"
    ) as repository_class:
        repository = repository_class.return_value
        repository.get_owned = AsyncMock(return_value=None)

        with pytest.raises(NotFoundException):
            await get_ingestion_job(
                job_id=job_id,
                session=session,
                current_user=current_user,
            )

        repository.get_owned.assert_awaited_once_with(
            job_id=job_id,
            owner_id=user_id,
        )

        repository.get_by_id.assert_not_called()
