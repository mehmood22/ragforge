from uuid import uuid4

from ragforge.services.conversation_threads import (
    conversation_thread_id,
)


def test_thread_id_is_deterministic():
    owner_id = uuid4()
    document_id = uuid4()
    conversation_id = uuid4()

    first = conversation_thread_id(
        owner_id,
        document_id,
        conversation_id,
    )

    second = conversation_thread_id(
        owner_id,
        document_id,
        conversation_id,
    )

    assert first == second


def test_different_users_get_different_threads():
    document_id = uuid4()
    conversation_id = uuid4()

    first = conversation_thread_id(
        uuid4(),
        document_id,
        conversation_id,
    )

    second = conversation_thread_id(
        uuid4(),
        document_id,
        conversation_id,
    )

    assert first != second
