from abc import ABC, abstractmethod

from ..models import CleanedDocument, DocumentFormat, StructuredDocument


class BaseStructureDetector(ABC):
    @abstractmethod
    def detect(self, document: CleanedDocument) -> StructuredDocument:
        ...

    @abstractmethod
    def supported_formats(self) -> list[DocumentFormat]:
        ...
