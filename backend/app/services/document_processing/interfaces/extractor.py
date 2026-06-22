from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from ..models import (
    DocumentFormat,
    ExtractedDocument,
    PipelineError,
    RawDocument,
)


class ExtractionResult(BaseModel):
    document: ExtractedDocument | None = None
    error: PipelineError | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.document is not None and self.error is None

    @property
    def failed(self) -> bool:
        return self.error is not None


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, document: RawDocument) -> ExtractionResult:
        ...

    @abstractmethod
    def supported_formats(self) -> list[DocumentFormat]:
        ...
