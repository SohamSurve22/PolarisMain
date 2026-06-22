import traceback

from ..models import (
    DocumentFormat,
    ExtractedDocument,
    ExtractedMetadata,
    ExtractionWarning,
    PageInfo,
    RawDocument,
    CorruptedFileError,
    EmptyDocumentError,
    PasswordProtectedError,
    PipelineError,
)
from ..models.errors import ExtractorError
from ..interfaces import ExtractionResult
from .base import AbstractExtractor


class PDFExtractor(AbstractExtractor):
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.PDF]

    def extract(self, document: RawDocument) -> ExtractionResult:
        result = self._try_pymupdf(document)
        if result.success:
            return result
        if result.error and not result.error.recoverable:
            return result
        fallback = self._try_pdfplumber(document)
        if fallback.success:
            return fallback
        return result

    def _try_pymupdf(self, document: RawDocument) -> ExtractionResult:
        try:
            import fitz
        except ImportError:
            return ExtractionResult(
                error=ExtractorError(
                    error_code="EXTRACTOR_DEPENDENCY_MISSING",
                    stage="extract",
                    message="PyMuPDF (fitz) is not installed",
                    context={"document_id": document.id},
                )
            )

        try:
            doc = fitz.open(stream=document.content, filetype="pdf")
        except fitz.FileDataError:
            return ExtractionResult(
                error=CorruptedFileError(
                    message="The PDF file appears to be corrupted and cannot be read",
                    context={"document_id": document.id},
                )
            )
        except Exception as exc:
            return ExtractionResult(
                error=CorruptedFileError(
                    message=f"Failed to open PDF: {exc}",
                    context={"document_id": document.id, "exception": str(exc)},
                    recoverable=True,
                )
            )

        if doc.is_encrypted:
            doc.close()
            return ExtractionResult(
                error=PasswordProtectedError(
                    message="The PDF is password-protected. Please remove the password and re-upload",
                    context={"document_id": document.id},
                )
            )

        warnings: list[ExtractionWarning] = []
        pages: list[PageInfo] = []
        text_parts: list[str] = []

        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                pages.append(
                    PageInfo(
                        page_number=page_num + 1,
                        text=page_text,
                        char_count=len(page_text),
                    )
                )
                text_parts.append(page_text)
            except Exception as exc:
                warnings.append(
                    ExtractionWarning(
                        code="PAGE_EXTRACTION_FAILED",
                        message=f"Failed to extract text from page {page_num + 1}: {exc}",
                        page=page_num + 1,
                    )
                )

        doc.close()

        full_text = "\n".join(text_parts)

        if not full_text.strip() and not warnings:
            return ExtractionResult(
                error=EmptyDocumentError(
                    message="This document appears to be empty",
                    context={"document_id": document.id},
                )
            )

        detected_lang, lang_conf = self._detect_language(full_text)

        metadata = self._compute_metadata(
            full_text=full_text,
            pages=pages,
            language=detected_lang,
            language_confidence=lang_conf,
            extraction_strategy="pymupdf",
        )

        extracted = self._build_extracted_document(
            raw_id=document.id,
            format=document.format,
            full_text=full_text,
            pages=pages,
            metadata=metadata,
            warnings=warnings,
        )

        return ExtractionResult(document=extracted)

    def _try_pdfplumber(self, document: RawDocument) -> ExtractionResult:
        try:
            import pdfplumber
        except ImportError:
            return ExtractionResult(
                error=ExtractorError(
                    error_code="EXTRACTOR_DEPENDENCY_MISSING",
                    stage="extract",
                    message="pdfplumber is not installed",
                    context={"document_id": document.id},
                    recoverable=True,
                )
            )

        try:
            import io
            with pdfplumber.open(io.BytesIO(document.content)) as pdf:
                warnings: list[ExtractionWarning] = []
                pages: list[PageInfo] = []
                text_parts: list[str] = []

                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text() or ""
                        pages.append(
                            PageInfo(
                                page_number=i + 1,
                                text=page_text,
                                char_count=len(page_text),
                            )
                        )
                        text_parts.append(page_text)
                    except Exception as exc:
                        warnings.append(
                            ExtractionWarning(
                                code="PAGE_EXTRACTION_FAILED",
                                message=f"pdfplumber failed on page {i + 1}: {exc}",
                                page=i + 1,
                            )
                        )

                full_text = "\n".join(text_parts)

                if not full_text.strip() and not warnings:
                    return ExtractionResult(
                        error=EmptyDocumentError(
                            message="This document appears to be empty",
                            context={"document_id": document.id},
                        )
                    )

                detected_lang, lang_conf = self._detect_language(full_text)

                metadata = self._compute_metadata(
                    full_text=full_text,
                    pages=pages,
                    language=detected_lang,
                    language_confidence=lang_conf,
                    extraction_strategy="pdfplumber",
                )

                extracted = self._build_extracted_document(
                    raw_id=document.id,
                    format=document.format,
                    full_text=full_text,
                    pages=pages,
                    metadata=metadata,
                    warnings=warnings,
                )

                return ExtractionResult(document=extracted)

        except Exception as exc:
            return ExtractionResult(
                error=CorruptedFileError(
                    message=f"pdfplumber also failed: {exc}",
                    context={"document_id": document.id, "exception": str(exc)},
                    recoverable=False,
                )
            )
