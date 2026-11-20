import logging

from ragforge.storage.base import FileStorage

logger = logging.getLogger(__name__)


async def delete_file_safely(
    storage: FileStorage,
    key: str,
) -> None:
    try:
        await storage.delete(key)
    except Exception:
        logger.exception(
            "Storage cleanup failed",
            extra={"storage_key": key},
        )
