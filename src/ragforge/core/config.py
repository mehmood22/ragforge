import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAGForge"
    environment: str = "development"
    debug: bool = False

    database_url: str

    chroma_host: str = "chroma"
    chroma_port: int = 8000
    chroma_collection: str = "ragforge_documents"

    storage_provider: str = "local"
    upload_directory: Path = Path("/app/uploads")
    max_upload_bytes: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
    )
    max_pdf_pages: int = 100

    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

    chunk_size: int = Field(default=800, gt=0)
    chunk_overlap: int = Field(default=120, ge=0)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    log_level: str = "INFO"
    log_to_file: bool = True
    log_dir: Path = Path("/app/logs")
    log_file_prefix: str = "ragforge"
    log_backup_days: int = 14

    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_min_score: float = Field(default=0.35, ge=0, le=1)

    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    llm_temperature: float = Field(default=0.0, ge=0, le=2)
    llm_max_tokens: int = Field(default=700, ge=100, le=4096)
    rag_max_context_chars: int = Field(default=12000, ge=1000, le=50000)

    model_config = SettingsConfigDict(
        env_file=os.environ.get("RAGFORGE_ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        if self.storage_provider not in {"local", "cloudinary"}:
            raise ValueError("Unsupported storage provider")

        if self.storage_provider == "cloudinary" and not all(
            (
                self.cloudinary_cloud_name,
                self.cloudinary_api_key,
                self.cloudinary_api_secret,
            )
        ):
            raise ValueError("Cloudinary credentials are required")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
