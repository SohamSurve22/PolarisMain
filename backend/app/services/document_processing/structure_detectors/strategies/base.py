from abc import ABC, abstractmethod

from ...models import CleanedDocument, DocumentStructure


class StructureDetectionStrategy(ABC):
    @property
    @abstractmethod
    def operation(self) -> str:
        ...

    @abstractmethod
    def process(self, document: CleanedDocument, structure: DocumentStructure | None = None) -> DocumentStructure:
        ...
