import pytest

from backend.app.services.document_processing.models import (
    DocumentFormat,
    EmptyDocumentError,
)
from backend.app.services.document_processing.extractors import TxtExtractor


class TestTxtExtractor:
    def setup_method(self):
        self.extractor = TxtExtractor()

    def test_supported_formats(self):
        assert self.extractor.supported_formats() == [DocumentFormat.TXT]

    def test_extract_valid_txt(self, raw_txt):
        result = self.extractor.extract(raw_txt)
        assert result.success, f"Extraction failed: {result.error}"
        assert result.document is not None
        assert result.document.format == DocumentFormat.TXT
        assert result.document.raw_id == raw_txt.id
        assert "Data Retention Policy" in result.document.text
        assert "IT Act 2000" in result.document.text

    def test_extract_txt_metadata(self, raw_txt):
        result = self.extractor.extract(raw_txt)
        assert result.success
        meta = result.document.metadata
        assert meta.extraction_strategy == "chardet"
        assert meta.word_count > 30
        assert meta.page_count == 1
        assert meta.language is not None

    def test_txt_has_single_page(self, raw_txt):
        result = self.extractor.extract(raw_txt)
        assert result.success
        pages = result.document.pages
        assert len(pages) == 1
        assert pages[0].page_number == 1
        assert pages[0].char_count > 0

    def test_empty_document_returns_error(self):
        from backend.tests.conftest import _make_raw_document
        raw = _make_raw_document(b"", "empty.txt", DocumentFormat.TXT)
        result = self.extractor.extract(raw)
        assert result.failed
        assert isinstance(result.error, EmptyDocumentError)

    def test_utf8_with_bom(self):
        from backend.tests.conftest import _make_raw_document
        content = "\ufeffTest content with BOM.\nLine two.".encode("utf-8-sig")
        raw = _make_raw_document(content, "bom.txt", DocumentFormat.TXT)
        result = self.extractor.extract(raw)
        assert result.success
        assert "Test content" in result.document.text

    def test_idempotent_same_input(self, sample_txt_content, raw_txt):
        result1 = self.extractor.extract(raw_txt)
        result2 = self.extractor.extract(
            raw_txt.model_copy(update={"id": "diff-id"})
        )
        assert result1.success and result2.success
        assert result1.document.text == result2.document.text
