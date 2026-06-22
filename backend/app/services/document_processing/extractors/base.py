from abc import ABC
from typing import Any

import chardet

from ..models import (
    DocumentFormat,
    ExtractedMetadata,
    ExtractedDocument,
    ExtractionWarning,
    PageInfo,
    PipelineError,
    RawDocument,
)
from ..interfaces import BaseExtractor, ExtractionResult


class AbstractExtractor(BaseExtractor, ABC):
    def _detect_language(self, text: str) -> tuple[str | None, float | None]:
        try:
            from langdetect import DetectorFactory, detect_langs
            DetectorFactory.seed = 0
            if not text.strip():
                return None, None
            langs = detect_langs(text[:2000])
            if langs:
                return langs[0].lang, langs[0].prob
        except Exception:
            pass
        return None, None

    def _compute_word_count(self, text: str) -> int:
        return len(text.split())

    def _compute_char_count(self, text: str) -> int:
        return len(text)

    def _compute_metadata(
        self,
        full_text: str,
        pages: list[PageInfo],
        language: str | None = None,
        language_confidence: float | None = None,
        extraction_strategy: str = "unknown",
        has_images: bool = False,
        has_tables: bool = False,
        is_scanned: bool = False,
    ) -> ExtractedMetadata:
        return ExtractedMetadata(
            word_count=self._compute_word_count(full_text),
            char_count=self._compute_char_count(full_text),
            page_count=len(pages) if pages else None,
            language=language,
            language_confidence=language_confidence,
            has_images=has_images,
            has_tables=has_tables,
            extraction_strategy=extraction_strategy,
            is_scanned=is_scanned,
        )

    def _build_extracted_document(
        self,
        raw_id: str,
        format: DocumentFormat,
        full_text: str,
        pages: list[PageInfo],
        metadata: ExtractedMetadata,
        warnings: list[ExtractionWarning] | None = None,
    ) -> ExtractedDocument:
        return ExtractedDocument(
            raw_id=raw_id,
            format=format,
            text=full_text,
            pages=pages,
            metadata=metadata,
            warnings=warnings or [],
        )

    def _encoding_from_bytes(self, content: bytes) -> str:
        result = chardet.detect(content)
        return result.get("encoding", "utf-8") or "utf-8"
