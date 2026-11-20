import asyncio
from pathlib import Path
from uuid import uuid4


class LocalFileStorage:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)

    async def save_bytes(self, content: bytes, extension: str = ".pdf") -> Path:
        clean_ext = extension if extension.startswith(".") else f".{extension}"
        stored_path = self.base_dir / f"{uuid4()}{clean_ext}"

        await asyncio.to_thread(self._write_file, self.base_dir, stored_path, content)
        return stored_path

    async def delete_file(self, file_path: Path) -> None:
        await asyncio.to_thread(file_path.unlink, True)

    @staticmethod
    def _write_file(base_dir: Path, stored_path: Path, content: bytes) -> None:
        base_dir.mkdir(parents=True, exist_ok=True)
        stored_path.write_bytes(content)