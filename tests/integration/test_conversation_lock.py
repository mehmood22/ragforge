from uuid import uuid4

import pytest

from ragforge.core.exceptions import ConflictException
from ragforge.infrastructure.conversation_lock import (
    conversation_lock,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_same_conversation_cannot_be_locked_twice() -> None:
    conversation_id = uuid4()

    async with conversation_lock(conversation_id):
        with pytest.raises(ConflictException):
            async with conversation_lock(conversation_id):
                pytest.fail("Second request acquired an existing lock")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_different_conversations_can_run_together() -> None:
    first_conversation = uuid4()
    second_conversation = uuid4()

    async with (
        conversation_lock(first_conversation),
        conversation_lock(second_conversation),
    ):
        assert True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lock_is_released_after_success() -> None:
    conversation_id = uuid4()

    async with conversation_lock(conversation_id):
        pass

    # This must succeed after the first lock is released.
    async with conversation_lock(conversation_id):
        assert True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lock_is_released_after_exception() -> None:
    conversation_id = uuid4()

    with pytest.raises(RuntimeError):
        async with conversation_lock(conversation_id):
            raise RuntimeError("Simulated LLM failure")

    # The failed request must not leave the lock held.
    async with conversation_lock(conversation_id):
        assert True
