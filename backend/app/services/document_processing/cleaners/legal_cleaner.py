from ..models import (
    CleanedDocument,
    CleaningStats,
    DocumentFormat,
    ExtractedDocument,
)
from ..models.config import CleanerConfig
from ..interfaces import BaseCleaner
from .strategies import (
    CleaningStrategy,
    HeaderFooterRemover,
    LineMerger,
    PageNumberRemover,
    ParagraphReconstructor,
    QuotationNormalizer,
    UnicodeNormalizer,
    WhitespaceNormalizer,
)


class LegalCleaner(BaseCleaner):
    def __init__(self, config: CleanerConfig | None = None):
        self._config = config or CleanerConfig()

    def supported_formats(self) -> list[DocumentFormat]:
        return [f for f in DocumentFormat]

    def clean(self, document: ExtractedDocument) -> CleanedDocument:
        strategies = self._build_strategy_chain()
        text = document.text
        pages = document.pages if document.pages else None
        all_operations: list[str] = []
        total_removed = 0

        for strategy in strategies:
            try:
                result = strategy.clean(text, pages)
                if result.was_modified:
                    text = result.text
                    all_operations.append(strategy.operation.value)
                    removed = result.stats.get("total_lines_removed", 0)
                    if not removed:
                        removed = result.stats.get("page_numbers_removed", 0)
                    total_removed += removed
            except Exception:
                continue

        stats = CleaningStats(
            original_char_count=document.metadata.char_count,
            cleaned_char_count=len(text),
            removed_char_count=max(0, document.metadata.char_count - len(text)),
            operations_applied=[op for op in self._config.enabled_operations if op.value in all_operations],
        )

        return CleanedDocument(
            extracted_id=document.raw_id,
            text=text,
            stats=stats,
        )

    def _build_strategy_chain(self) -> list[CleaningStrategy]:
        enabled = {op.value for op in self._config.enabled_operations}
        chain: list[CleaningStrategy] = []

        strategy_map: dict[str, type[CleaningStrategy]] = {
            "normalize_unicode": UnicodeNormalizer,
            "normalize_whitespace": WhitespaceNormalizer,
            "normalize_quotes": QuotationNormalizer,
            "remove_non_textual_artifacts": LineMerger,
            "merge_lines": LineMerger,
            "remove_headers": HeaderFooterRemover,
            "remove_footers": HeaderFooterRemover,
            "remove_page_numbers": PageNumberRemover,
            "reconstruct_paragraphs": ParagraphReconstructor,
            "collapse_blank_lines": ParagraphReconstructor,
        }

        seen_types: set[type] = set()
        for op_value in [
            "normalize_unicode",
            "normalize_whitespace",
            "normalize_quotes",
            "merge_lines",
            "remove_headers",
            "remove_footers",
            "remove_page_numbers",
            "reconstruct_paragraphs",
            "collapse_blank_lines",
        ]:
            if op_value not in enabled:
                continue
            strategy_cls = strategy_map.get(op_value)
            if strategy_cls is None:
                continue
            if strategy_cls in seen_types:
                continue
            seen_types.add(strategy_cls)

            if strategy_cls is HeaderFooterRemover:
                instance = strategy_cls(
                    min_pages=self._config.header_footer_min_pages,
                    match_threshold=self._config.header_footer_match_threshold,
                )
            elif strategy_cls is WhitespaceNormalizer:
                instance = strategy_cls(
                    max_consecutive_blank_lines=self._config.max_consecutive_blank_lines,
                )
            elif strategy_cls is LineMerger:
                instance = strategy_cls(
                    merge_hyphenated=self._config.merge_hyphenated_words,
                    merge_continuation=self._config.merge_continuation_lines,
                )
            elif strategy_cls is ParagraphReconstructor:
                instance = strategy_cls(
                    preserve_list_indentation=self._config.preserve_list_indentation,
                )
            else:
                instance = strategy_cls()

            chain.append(instance)

        return chain
