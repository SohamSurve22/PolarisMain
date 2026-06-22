import pytest

from backend.app.services.document_processing.models import DocumentFormat
from backend.app.services.document_processing.extractors import (
    PDFExtractor,
    DOCXExtractor,
    TxtExtractor,
    HtmlExtractor,
    ExtractorRegistry,
)
from backend.app.services.document_processing.interfaces import BaseExtractor


class TestExtractorRegistry:
    def setup_method(self):
        ExtractorRegistry.reset()

    def test_returns_pdf_extractor(self):
        extractor = ExtractorRegistry.get_extractor(DocumentFormat.PDF)
        assert isinstance(extractor, PDFExtractor)

    def test_returns_docx_extractor(self):
        extractor = ExtractorRegistry.get_extractor(DocumentFormat.DOCX)
        assert isinstance(extractor, DOCXExtractor)

    def test_returns_txt_extractor(self):
        extractor = ExtractorRegistry.get_extractor(DocumentFormat.TXT)
        assert isinstance(extractor, TxtExtractor)

    def test_returns_html_extractor(self):
        extractor = ExtractorRegistry.get_extractor(DocumentFormat.HTML)
        assert isinstance(extractor, HtmlExtractor)

    def test_all_extractors_implement_interface(self):
        for fmt in DocumentFormat:
            extractor = ExtractorRegistry.get_extractor(fmt)
            assert isinstance(extractor, BaseExtractor)
            assert fmt in extractor.supported_formats()

    def test_supported_formats(self):
        formats = ExtractorRegistry.supported_formats()
        assert DocumentFormat.PDF in formats
        assert DocumentFormat.DOCX in formats
        assert DocumentFormat.TXT in formats
        assert DocumentFormat.HTML in formats

    def test_register_custom_extractor(self):
        class StubExtractor(BaseExtractor):
            def extract(self, document):
                from backend.app.services.document_processing.interfaces import ExtractionResult
                return ExtractionResult()
            def supported_formats(self):
                return [DocumentFormat.PDF]

        ExtractorRegistry.register(DocumentFormat.PDF, StubExtractor())
        extractor = ExtractorRegistry.get_extractor(DocumentFormat.PDF)
        assert isinstance(extractor, StubExtractor)

    def test_registry_extracts_all_formats(self, raw_pdf, raw_docx, raw_txt, raw_html):
        documents = [
            (raw_pdf, DocumentFormat.PDF),
            (raw_docx, DocumentFormat.DOCX),
            (raw_txt, DocumentFormat.TXT),
            (raw_html, DocumentFormat.HTML),
        ]
        for raw, fmt in documents:
            extractor = ExtractorRegistry.get_extractor(fmt)
            result = extractor.extract(raw)
            assert result.success, f"Failed to extract {fmt.value}: {result.error}"
            assert result.document.format == fmt
