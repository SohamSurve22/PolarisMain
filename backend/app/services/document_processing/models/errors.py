from typing import Any

from pydantic import BaseModel, Field


class PipelineError(BaseModel):
    error_code: str
    stage: str
    message: str
    is_fatal: bool = True
    recoverable: bool = False
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class CorruptedFileError(PipelineError):
    error_code: str = "CORRUPTED_PDF"
    stage: str = "extract"
    is_fatal: bool = True
    recoverable: bool = False


class PasswordProtectedError(PipelineError):
    error_code: str = "PASSWORD_PROTECTED_PDF"
    stage: str = "extract"
    is_fatal: bool = True
    recoverable: bool = False


class EmptyDocumentError(PipelineError):
    error_code: str = "EMPTY_DOCUMENT"
    stage: str = "extract"
    is_fatal: bool = True
    recoverable: bool = False


class UnsupportedFormatError(PipelineError):
    error_code: str = "INVALID_FILE_TYPE"
    stage: str = "extract"
    is_fatal: bool = True
    recoverable: bool = False


class FileTooLargeError(PipelineError):
    error_code: str = "FILE_TOO_LARGE"
    stage: str = "extract"
    is_fatal: bool = True
    recoverable: bool = False


class PageLimitExceededError(PipelineError):
    error_code: str = "PAGE_LIMIT_EXCEEDED"
    stage: str = "extract"
    is_fatal: bool = True
    recoverable: bool = False


class ExtractorError(PipelineError):
    error_code: str = "EXTRACTION_FAILED"
    stage: str = "extract"
    is_fatal: bool = True
    recoverable: bool = True


class CleaningError(PipelineError):
    error_code: str = "CLEANING_FAILED"
    stage: str = "clean"
    is_fatal: bool = False
    recoverable: bool = True


class StructureDetectionError(PipelineError):
    error_code: str = "STRUCTURE_DETECTION_FAILED"
    stage: str = "structure_detect"
    is_fatal: bool = False
    recoverable: bool = True


class NoClausesFoundError(PipelineError):
    error_code: str = "NO_LEGAL_CLAUSES"
    stage: str = "clause_extract"
    is_fatal: bool = False
    recoverable: bool = False


class ClauseExtractionError(PipelineError):
    error_code: str = "CLAUSE_EXTRACTION_FAILED"
    stage: str = "clause_extract"
    is_fatal: bool = False
    recoverable: bool = True
