from functools import lru_cache

from ragforge.core.config import get_settings
from ragforge.storage.base import FileStorage
from ragforge.storage.local import LocalFileStorage


@lru_cache
def get_storage() -> FileStorage:
    settings = get_settings()

    if settings.storage_provider == "local":
        return LocalFileStorage(settings.upload_directory)

    if settings.storage_provider == "cloudinary":
        from ragforge.storage.cloudinary import CloudinaryFileStorage

        return CloudinaryFileStorage(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
        )

    raise ValueError("Unsupported storage provider")
