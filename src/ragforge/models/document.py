from enum import Enum

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ragforge.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class SourceType(str, Enum):
    PDF = "pdf"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    TEXT = "text"
    IMAGE = "image"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "documents"

    __table_args__ = (
        CheckConstraint(
            "chunk_count >= 0",
            name="ck_documents_chunk_count",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    source_uri: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=DocumentStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
