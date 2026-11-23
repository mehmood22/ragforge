from uuid import UUID


def conversation_thread_id(
    owner_id: UUID,
    document_id: UUID,
    conversation_id: UUID,
) -> str:
    return f"{owner_id}:{document_id}:{conversation_id}"
