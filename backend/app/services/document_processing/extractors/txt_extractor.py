from ..models import (
    DocumentFormat,
    ExtractedDocument,
    ExtractedMetadata,
    PageInfo,
    RawDocument,
    EmptyDocumentError,
)
from ..models.errors import ExtractorError
from ..interfaces import ExtractionResult
from .base import AbstractExtractor


class TxtExtractor(AbstractExtractor):
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.TXT]

    def extract(self, document: RawDocument) -> ExtractionResult:
        encoding = self._encoding_from_bytes(document.content)

        try:
            text = document.content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            try:
                text = document.content.decode("utf-8", errors="replace")
            except Exception as exc:
                return ExtractionResult(
                    error=ExtractorError(
                        error_code="TXT_DECODE_FAILED",
                        stage="extract",
                        message=f"Failed to decode text file: {exc}",
                        context={"document_id": document.id, "encoding": encoding},
                    )
                )

        text = text.strip()

        if not text:
            return ExtractionResult(
                error=EmptyDocumentError(
                    message="This document appears to be empty",
                    context={"document_id": document.id},
                )
            )

        lines = text.split("\n")
        single_page_text = "\n".join(lines)

        page = PageInfo(
            page_number=1,
            text=single_page_text,
            char_count=len(single_page_text),
        )

        detected_lang, lang_conf = self._detect_language(single_page_text)

        metadata = self._compute_metadata(
            full_text=single_page_text,
            pages=[page],
            language=detected_lang,
            language_confidence=lang_conf,
            extraction_strategy="chardet",
        )

        extracted = self._build_extracted_document(
            raw_id=document.id,
            format=document.format,
            full_text=single_page_text,
            pages=[page],
            metadata=metadata,
        )

        return ExtractionResult(document=extracted)
