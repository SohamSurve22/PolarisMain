from ..interfaces import BaseClauseExtractor
from ..models import (
    ClauseDocument,
    ClauseExtractorConfig,
    CleanedDocument,
    DocumentFormat,
    StructuredDocument,
)
from .strategies.base import ClauseExtractionStrategy
from .strategies.clause_builder import ClauseBuilderStrategy


class ClauseExtractor(BaseClauseExtractor):
    def __init__(self, config: ClauseExtractorConfig | None = None):
        self._config = config or ClauseExtractorConfig()

    def supported_formats(self) -> list[DocumentFormat]:
        return [f for f in DocumentFormat]

    def extract(self, document: CleanedDocument, structure: StructuredDocument) -> ClauseDocument:
        result = ClauseBuilderStrategy().process(document, structure)
        object.__setattr__(result, "extraction_strategy", "hierarchical")
        return result
