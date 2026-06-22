from pydantic import BaseModel, Field

from .enums import CleaningOperation, DocumentFormat


class DocumentStatistics(BaseModel):
    format: DocumentFormat
    filename: str
    file_size_bytes: int = Field(ge=0)
    checksum_sha256: str

    word_count: int = Field(ge=0)
    char_count: int = Field(ge=0)
    cleaned_char_count: int | None = None
    removed_char_count: int | None = None
    page_count: int | None = Field(default=None, ge=0)
    language: str | None = None
    language_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    has_images: bool = False
    has_tables: bool = False
    is_scanned: bool = False

    structural_element_count: int = Field(ge=0)
    section_count: int = Field(ge=0)
    clause_count: int = Field(ge=0)
    root_clause_count: int = Field(ge=0)

    cleaning_operations_applied: list[CleaningOperation] = Field(default_factory=list)

    model_config = {"frozen": True}
