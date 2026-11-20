from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAGForge"
    environment: str = "development"
    debug: bool = False

    database_url: str

    chroma_host: str = "chroma"
    chroma_port: int = 8000

    upload_directory: str = "/app/uploads"
    max_pdf_pages: int = 100
    max_upload_bytes: int = 10 * 1024 * 1024
    chunk_size: int = 800
    chunk_overlap: int = 120
    embedding_model: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    chroma_collection: str = "ragforge_documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
