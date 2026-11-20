from pathlib import Path

import pytest

from ragforge.storage.local import LocalFileStorage


@pytest.mark.asyncio
async def test_local_storage_lifecycle(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    result = await storage.upload(
        key="example.pdf",
        content=b"%PDF-test-content",
    )

    assert result.key == "example.pdf"
    assert result.size == len(b"%PDF-test-content")

    content = await storage.download("example.pdf")
    assert content == b"%PDF-test-content"

    await storage.delete("example.pdf")

    assert not (tmp_path / "example.pdf").exists()


@pytest.mark.asyncio
async def test_reject_path_traversal(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    with pytest.raises(ValueError):
        await storage.upload(
            key="../secret.txt",
            content=b"secret",
        )


@pytest.mark.asyncio
async def test_prevent_overwriting_files(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    await storage.upload("same.pdf", b"first")

    with pytest.raises(FileExistsError):
        await storage.upload("same.pdf", b"second")

    assert await storage.download("same.pdf") == b"first"
