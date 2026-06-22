from .clauses import Clause, ClauseDocument
from .cleaning import CleanedDocument, CleaningStats
from .config import (
    CleanerConfig,
    ClauseExtractorConfig,
    ExtractorConfig,
    PipelineConfig,
    StructureDetectorConfig,
)
from .document import ExtractedMetadata, PageInfo, RawDocument
from .enums import (
    CleaningOperation,
    DocumentFormat,
    DocumentType,
    ProcessingStatus,
    StructuralElementType,
)
from .errors import (
    ClauseExtractionError,
    CleaningError,
    CorruptedFileError,
    EmptyDocumentError,
    ExtractorError,
    FileTooLargeError,
    NoClausesFoundError,
    PageLimitExceededError,
    PasswordProtectedError,
    PipelineError,
    StructureDetectionError,
    UnsupportedFormatError,
)
from .extraction import ExtractedDocument, ExtractionWarning
from .ir import CanonicalIntermediateRepresentation, IRMetadata, StageTiming, ValidationInfo
from .statistics import DocumentStatistics
from .structure import (
    BoundingBox,
    DocumentStructure,
    StructuralElement,
    StructuredDocument,
    TableOfContents,
    TableOfContentsEntry,
)
from .validation import UploadValidationResult, ValidationError

__all__ = [
    # Enums
    "DocumentFormat",
    "DocumentType",
    "ProcessingStatus",
    "CleaningOperation",
    "StructuralElementType",
    # Document
    "RawDocument",
    "PageInfo",
    "ExtractedMetadata",
    # Extraction
    "ExtractedDocument",
    "ExtractionWarning",
    # Cleaning
    "CleanedDocument",
    "CleaningStats",
    # Structure
    "BoundingBox",
    "StructuralElement",
    "TableOfContentsEntry",
    "TableOfContents",
    "DocumentStructure",
    "StructuredDocument",
    # Clauses
    "Clause",
    "ClauseDocument",
    # IR
    "CanonicalIntermediateRepresentation",
    "IRMetadata",
    "StageTiming",
    "ValidationInfo",
    "DocumentStatistics",
    # Config
    "PipelineConfig",
    "ExtractorConfig",
    "CleanerConfig",
    "StructureDetectorConfig",
    "ClauseExtractorConfig",
    # Errors
    "PipelineError",
    "CorruptedFileError",
    "PasswordProtectedError",
    "EmptyDocumentError",
    "UnsupportedFormatError",
    "FileTooLargeError",
    "PageLimitExceededError",
    "ExtractorError",
    "CleaningError",
    "StructureDetectionError",
    "NoClausesFoundError",
    "ClauseExtractionError",
    # Validation
    "UploadValidationResult",
    "ValidationError",
]
