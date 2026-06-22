from pydantic import BaseModel, Field

from .enums import DocumentFormat


class ValidationError(BaseModel):
    code: str
    message: str
    field: str | None = None


class UploadValidationResult(BaseModel):
    is_valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    detected_format: DocumentFormat | None = None
    checksum_sha256: str | None = None
    size_bytes: int | None = None
    page_count: int | None = None
