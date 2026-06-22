import pytest

from backend.app.services.document_processing.models import (
    DocumentFormat,
    EmptyDocumentError,
)
from backend.app.services.document_processing.extractors import DOCXExtractor


class TestDOCXExtractor:
    def setup_method(self):
        self.extractor = DOCXExtractor()

    def test_supported_formats(self):
        assert self.extractor.supported_formats() == [DocumentFormat.DOCX]

    def test_extract_valid_docx(self, raw_docx):
        result = self.extractor.extract(raw_docx)
        assert result.success, f"Extraction failed: {result.error}"
        assert result.document is not None
        assert result.document.format == DocumentFormat.DOCX
        assert result.document.raw_id == raw_docx.id
        assert "Terms of Service" in result.document.text
        assert "Governing Law" in result.document.text
        assert "India" in result.document.text

    def test_extract_docx_metadata(self, raw_docx):
        result = self.extractor.extract(raw_docx)
        assert result.success
        meta = result.document.metadata
        assert meta.extraction_strategy == "python-docx"
        assert meta.word_count > 20
        assert meta.char_count > 100
        assert meta.page_count is None
        assert meta.language is not None

    def test_docx_no_page_concept(self, raw_docx):
        result = self.extractor.extract(raw_docx)
        assert result.success
        assert len(result.document.pages) == 0

    def test_empty_document_returns_error(self):
        from backend.tests.conftest import _make_raw_document
        from backend.app.services.document_processing.models import RawDocument
        raw = _make_raw_document(
            b"\x50\x4B\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            "empty.docx", DocumentFormat.DOCX,
        )
        result = self.extractor.extract(raw)
        assert result.failed

    def test_idempotent_same_input(self, sample_docx_content, raw_docx):
        result1 = self.extractor.extract(raw_docx)
        result2 = self.extractor.extract(
            raw_docx.model_copy(update={"id": "diff-id"})
        )
        assert result1.success and result2.success
        assert result1.document.text == result2.document.text
