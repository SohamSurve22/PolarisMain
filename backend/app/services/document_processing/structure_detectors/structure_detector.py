from ..interfaces import BaseStructureDetector
from ..models import (
    CleanedDocument,
    DocumentFormat,
    DocumentStructure,
    StructureDetectorConfig,
    StructureDetectionError,
    StructuredDocument,
)
from .strategies.base import StructureDetectionStrategy
from .strategies.heading_detector import HeadingDetectionStrategy
from .strategies.hierarchy_builder import HierarchyBuildingStrategy
from .strategies.toc_detector import TOCDetectionStrategy


class StructureDetector(BaseStructureDetector):
    def __init__(self, config: StructureDetectorConfig | None = None):
        self._config = config or StructureDetectorConfig()

    def supported_formats(self) -> list[DocumentFormat]:
        return [f for f in DocumentFormat]

    def detect(self, document: CleanedDocument) -> StructuredDocument:
        strategies = self._build_strategy_chain()
        structure = DocumentStructure(detection_strategy="structure_detector")

        for strategy in strategies:
            try:
                structure = strategy.process(document, structure)
            except Exception as exc:
                raise StructureDetectionError(
                    message=f"Strategy '{strategy.operation}' failed: {exc}",
                    context={"strategy": strategy.operation},
                ) from exc

        return StructuredDocument(
            cleaned_id=document.extracted_id,
            structure=structure,
        )

    def _build_strategy_chain(self) -> list[StructureDetectionStrategy]:
        chain: list[StructureDetectionStrategy] = []

        chain.append(HeadingDetectionStrategy(
            min_confidence=self._config.min_heading_confidence,
            custom_patterns=self._config.heading_patterns,
        ))

        chain.append(HierarchyBuildingStrategy())

        if self._config.enable_toc_detection:
            chain.append(TOCDetectionStrategy())

        return chain
