from functools import lru_cache

import chromadb
from chromadb import HttpClient

from ragforge.core.config import get_settings


@lru_cache
def get_chroma_client() -> HttpClient:
    settings = get_settings()

    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )
