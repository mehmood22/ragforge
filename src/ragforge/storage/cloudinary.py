import asyncio

import cloudinary
import cloudinary.api
import cloudinary.uploader

from ragforge.storage.base import StoredFile


class CloudinaryFileStorage:
    def __init__(
        self,
        cloud_name: str | None,
        api_key: str | None,
        api_secret: str | None,
    ) -> None:
        if not all((cloud_name, api_key, api_secret)):
            raise ValueError("Missing Cloudinary configuration")

        self.config = cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )

    async def upload(
        self,
        key: str,
        content: bytes,
    ) -> StoredFile:
        def perform_upload() -> dict:
            return cloudinary.uploader.upload(
                content,
                resource_type="raw",
                public_id=f"ragforge/{key}",
                overwrite=False,
            )

        result = await asyncio.to_thread(perform_upload)

        return StoredFile(
            key=key,
            size=int(result["bytes"]),
        )

    async def download(self, key: str) -> bytes:
        raise NotImplementedError(
            "Authenticated Cloudinary download is not implemented yet"
        )

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(
            cloudinary.uploader.destroy,
            f"ragforge/{key}",
            resource_type="raw",
        )
