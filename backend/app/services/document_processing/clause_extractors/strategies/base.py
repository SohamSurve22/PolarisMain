from abc import ABC, abstractmethod

from ...models import (
    ClauseDocument,
    CleanedDocument,
    StructuredDocument,
)


class ClauseExtractionStrategy(ABC):
    @property
    @abstractmethod
    def operation(self) -> str:
        ...

    @abstractmethod
    def process(self, document: CleanedDocument, structure: StructuredDocument) -> ClauseDocument:
        ...
