from ..models import (
    DocumentFormat,
    ExtractionWarning,
    ExtractedDocument,
    ExtractedMetadata,
    PageInfo,
    RawDocument,
    EmptyDocumentError,
)
from ..models.errors import ExtractorError
from ..interfaces import ExtractionResult
from .base import AbstractExtractor


class HtmlExtractor(AbstractExtractor):
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.HTML]

    def extract(self, document: RawDocument) -> ExtractionResult:
        result = self._try_beautifulsoup(document)
        if result.success:
            return result

        fallback = self._try_trafilatura(document)
        if fallback.success:
            return fallback

        return result

    def _try_beautifulsoup(self, document: RawDocument) -> ExtractionResult:
        try:
            from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
            import warnings as _warnings
            _warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
        except ImportError:
            return ExtractionResult(
                error=ExtractorError(
                    error_code="EXTRACTOR_DEPENDENCY_MISSING",
                    stage="extract",
                    message="BeautifulSoup4 is not installed",
                    context={"document_id": document.id},
                    recoverable=True,
                )
            )

        encoding = self._encoding_from_bytes(document.content)

        try:
            html_content = document.content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            html_content = document.content.decode("utf-8", errors="replace")

        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception as exc:
            return ExtractionResult(
                error=ExtractorError(
                    error_code="HTML_PARSE_FAILED",
                    stage="extract",
                    message=f"Failed to parse HTML: {exc}",
                    context={"document_id": document.id, "exception": str(exc)},
                    recoverable=True,
                )
            )

        warnings: list[ExtractionWarning] = []

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        body = soup.find("body")
        if body is None:
            body = soup

        for unwanted in body.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            unwanted.decompose()

        text_parts: list[str] = []
        if title:
            text_parts.append(title)

        for element in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th", "blockquote"]):
            text = element.get_text(strip=True)
            if text:
                if element.name.startswith("h"):
                    text_parts.append(f"\n{text}\n")
                elif element.name == "li":
                    text_parts.append(f"  - {text}")
                else:
                    text_parts.append(text)

        full_text = "\n".join(text_parts).strip()

        if not full_text:
            return ExtractionResult(
                error=EmptyDocumentError(
                    message="This document appears to be empty",
                    context={"document_id": document.id},
                )
            )

        detected_lang, lang_conf = self._detect_language(full_text)

        page = PageInfo(
            page_number=1,
            text=full_text,
            char_count=len(full_text),
            metadata={"title": title} if title else {},
        )

        metadata = self._compute_metadata(
            full_text=full_text,
            pages=[page],
            language=detected_lang,
            language_confidence=lang_conf,
            extraction_strategy="beautifulsoup",
        )

        extracted = self._build_extracted_document(
            raw_id=document.id,
            format=document.format,
            full_text=full_text,
            pages=[page],
            metadata=metadata,
            warnings=warnings,
        )

        return ExtractionResult(document=extracted)

    def _try_trafilatura(self, document: RawDocument) -> ExtractionResult:
        try:
            import trafilatura
        except ImportError:
            return ExtractionResult(
                error=ExtractorError(
                    error_code="EXTRACTOR_DEPENDENCY_MISSING",
                    stage="extract",
                    message="trafilatura is not installed",
                    context={"document_id": document.id},
                    recoverable=True,
                )
            )

        encoding = self._encoding_from_bytes(document.content)

        try:
            html_content = document.content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            html_content = document.content.decode("utf-8", errors="replace")

        try:
            extracted_text = trafilatura.extract(html_content)
        except Exception as exc:
            return ExtractionResult(
                error=ExtractorError(
                    error_code="HTML_EXTRACTION_FAILED",
                    stage="extract",
                    message=f"trafilatura extraction failed: {exc}",
                    context={"document_id": document.id, "exception": str(exc)},
                )
            )

        if not extracted_text or not extracted_text.strip():
            return ExtractionResult(
                error=EmptyDocumentError(
                    message="This document appears to be empty",
                    context={"document_id": document.id},
                )
            )

        full_text = extracted_text.strip()

        detected_lang, lang_conf = self._detect_language(full_text)

        page = PageInfo(
            page_number=1,
            text=full_text,
            char_count=len(full_text),
        )

        metadata = self._compute_metadata(
            full_text=full_text,
            pages=[page],
            language=detected_lang,
            language_confidence=lang_conf,
            extraction_strategy="trafilatura",
        )

        extracted = self._build_extracted_document(
            raw_id=document.id,
            format=document.format,
            full_text=full_text,
            pages=[page],
            metadata=metadata,
        )

        return ExtractionResult(document=extracted)
