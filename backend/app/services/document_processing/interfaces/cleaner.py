from abc import ABC, abstractmethod

from ..models import CleanedDocument, DocumentFormat, ExtractedDocument


class BaseCleaner(ABC):
    @abstractmethod
    def clean(self, document: ExtractedDocument) -> CleanedDocument:
        ...

    @abstractmethod
    def supported_formats(self) -> list[DocumentFormat]:
        ...
