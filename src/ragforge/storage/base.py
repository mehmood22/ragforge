from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredFile:
    key: str
    size: int


class FileStorage(Protocol):
    async def upload(
        self,
        key: str,
        content: bytes,
    ) -> StoredFile: ...

    async def download(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...
