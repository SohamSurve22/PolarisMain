import pytest

from backend.app.services.document_processing.models import (
    DocumentFormat,
)
from backend.app.services.document_processing.extractors import PDFExtractor


class TestPDFExtractor:
    def setup_method(self):
        self.extractor = PDFExtractor()

    def test_supported_formats(self):
        assert self.extractor.supported_formats() == [DocumentFormat.PDF]

    def test_extract_valid_pdf(self, raw_pdf):
        result = self.extractor.extract(raw_pdf)
        assert result.success, f"Extraction failed: {result.error}"
        assert result.document is not None
        assert result.document.format == DocumentFormat.PDF
        assert result.document.raw_id == raw_pdf.id
        assert result.document.metadata.page_count == 1
        assert result.document.metadata.word_count > 0
        assert result.document.metadata.char_count > 0
        assert len(result.document.pages) == 1
        assert "Privacy Policy" in result.document.text
        assert "Digital Personal Data Protection Act 2023" in result.document.text

    def test_extract_pdf_metadata(self, raw_pdf):
        result = self.extractor.extract(raw_pdf)
        assert result.success
        meta = result.document.metadata
        assert meta.extraction_strategy == "pymupdf"
        assert meta.word_count > 50
        assert meta.char_count > 200
        assert meta.page_count == 1
        assert meta.language is not None

    def test_extract_pdf_pages(self, raw_pdf):
        result = self.extractor.extract(raw_pdf)
        assert result.success
        pages = result.document.pages
        assert len(pages) == 1
        assert pages[0].page_number == 1
        assert pages[0].char_count > 0

    def test_empty_bytes_fails(self, raw_empty):
        result = self.extractor.extract(raw_empty)
        assert result.failed

    def test_corrupted_pdf_returns_error(self, raw_corrupted_pdf):
        result = self.extractor.extract(raw_corrupted_pdf)
        assert result.failed
        assert result.error.error_code == "CORRUPTED_PDF"

    def test_idempotent_same_input(self, sample_pdf_content, raw_pdf):
        result1 = self.extractor.extract(raw_pdf)
        result2 = self.extractor.extract(
            raw_pdf.model_copy(update={"id": "diff-id"})
        )
        assert result1.success and result2.success
        assert result1.document.text == result2.document.text
        assert result1.document.metadata.char_count == result2.document.metadata.char_count
