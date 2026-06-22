from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .enums import DocumentFormat


class RawDocument(BaseModel):
    id: str
    filename: str
    format: DocumentFormat
    content: bytes
    size_bytes: int = Field(ge=0)
    checksum_sha256: str
    upload_timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("checksum_sha256")
    @classmethod
    def valid_sha256(cls, v: str) -> str:
        normalized = v.lower()
        if len(normalized) != 64 or not all(c in "0123456789abcdef" for c in normalized):
            raise ValueError("checksum_sha256 must be a 64-character lowercase hex string")
        return normalized

    model_config = {"frozen": True}


class PageInfo(BaseModel):
    page_number: int = Field(ge=1)
    text: str
    char_count: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedMetadata(BaseModel):
    word_count: int = Field(ge=0)
    char_count: int = Field(ge=0)
    page_count: int | None = Field(default=None, ge=0)
    language: str | None = Field(default=None, min_length=2, max_length=10)
    language_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    has_images: bool = False
    has_tables: bool = False
    extraction_strategy: str = "unknown"
    is_scanned: bool = False
