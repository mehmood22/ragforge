from uuid import uuid4

from ragforge.infrastructure.conversation_lock import (
    conversation_lock_key,
)


def test_same_conversation_has_same_lock_key() -> None:
    conversation_id = uuid4()

    first = conversation_lock_key(conversation_id)
    second = conversation_lock_key(conversation_id)

    assert first == second


def test_different_conversations_have_different_keys() -> None:
    first = conversation_lock_key(uuid4())
    second = conversation_lock_key(uuid4())

    assert first != second


def test_lock_key_fits_postgresql_bigint() -> None:
    key = conversation_lock_key(uuid4())

    assert -(2**63) <= key < 2**63
