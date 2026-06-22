from abc import ABC, abstractmethod

from ..models import ClauseDocument, CleanedDocument, DocumentFormat, StructuredDocument


class BaseClauseExtractor(ABC):
    @abstractmethod
    def extract(self, document: CleanedDocument, structure: StructuredDocument) -> ClauseDocument:
        ...

    @abstractmethod
    def supported_formats(self) -> list[DocumentFormat]:
        ...
