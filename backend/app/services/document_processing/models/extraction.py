from typing import Any

from pydantic import BaseModel, Field

from .document import ExtractedMetadata, PageInfo
from .enums import DocumentFormat


class ExtractionWarning(BaseModel):
    code: str
    message: str
    page: int | None = Field(default=None, ge=1)
    details: dict[str, Any] | None = None


class ExtractedDocument(BaseModel):
    raw_id: str
    format: DocumentFormat
    text: str
    pages: list[PageInfo] = Field(default_factory=list)
    metadata: ExtractedMetadata
    warnings: list[ExtractionWarning] = Field(default_factory=list)

    model_config = {"frozen": True}
