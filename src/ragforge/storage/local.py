import asyncio
from pathlib import Path

from ragforge.storage.base import StoredFile


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _resolve_path(self, key: str) -> Path:
        if not key or not key.isascii():
            raise ValueError("Invalid storage key")

        if not all(character.isalnum() or character in "-_." for character in key):
            raise ValueError("Invalid storage key")

        path = (self.root / key).resolve()

        if path.parent != self.root:
            raise ValueError("Invalid storage path")

        return path

    async def upload(
        self,
        key: str,
        content: bytes,
    ) -> StoredFile:
        path = self._resolve_path(key)

        def write_file() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("xb") as file:
                file.write(content)

        await asyncio.to_thread(write_file)

        return StoredFile(key=key, size=len(content))

    async def download(self, key: str) -> bytes:
        path = self._resolve_path(key)
        return await asyncio.to_thread(path.read_bytes)

    async def delete(self, key: str) -> None:
        path = self._resolve_path(key)
        await asyncio.to_thread(path.unlink, missing_ok=True)
