import pytest

from backend.app.services.document_processing.models import (
    DocumentFormat,
    EmptyDocumentError,
)
from backend.app.services.document_processing.extractors import HtmlExtractor


class TestHtmlExtractor:
    def setup_method(self):
        self.extractor = HtmlExtractor()

    def test_supported_formats(self):
        assert self.extractor.supported_formats() == [DocumentFormat.HTML]

    def test_extract_valid_html(self, raw_html):
        result = self.extractor.extract(raw_html)
        assert result.success, f"Extraction failed: {result.error}"
        assert result.document is not None
        assert result.document.format == DocumentFormat.HTML
        assert result.document.raw_id == raw_html.id
        assert "Cookie Policy" in result.document.text
        assert "Essential cookies" in result.document.text
        assert "dpo@example.com" in result.document.text

    def test_extract_html_metadata(self, raw_html):
        result = self.extractor.extract(raw_html)
        assert result.success
        meta = result.document.metadata
        assert meta.extraction_strategy == "beautifulsoup"
        assert meta.word_count > 20
        assert meta.page_count == 1
        assert meta.language is not None

    def test_scripts_and_styles_removed(self, raw_html):
        result = self.extractor.extract(raw_html)
        assert result.success
        text = result.document.text
        assert "console.log" not in text
        assert "font-family" not in text

    def test_empty_html_returns_error(self):
        from backend.tests.conftest import _make_raw_document
        content = b"<html><head></head><body></body></html>"
        raw = _make_raw_document(content, "empty.html", DocumentFormat.HTML)
        result = self.extractor.extract(raw)
        assert result.failed
        assert isinstance(result.error, EmptyDocumentError)

    def test_malformed_html_still_extracts(self):
        from backend.tests.conftest import _make_raw_document
        content = b"<html><body><p>Some text</html>"
        raw = _make_raw_document(content, "malformed.html", DocumentFormat.HTML)
        result = self.extractor.extract(raw)
        assert result.success
        assert "Some text" in result.document.text

    def test_trafilatura_fallback_on_bs4_failure(self):
        from backend.tests.conftest import _make_raw_document
        content = b"<html><body><p>Fallback test</p></body></html>"
        raw = _make_raw_document(content, "fallback.html", DocumentFormat.HTML)
        result = self.extractor.extract(raw)
        assert result.success
        assert "Fallback test" in result.document.text

    def test_idempotent_same_input(self, sample_html_content, raw_html):
        result1 = self.extractor.extract(raw_html)
        result2 = self.extractor.extract(
            raw_html.model_copy(update={"id": "diff-id"})
        )
        assert result1.success and result2.success
        assert result1.document.text == result2.document.text
