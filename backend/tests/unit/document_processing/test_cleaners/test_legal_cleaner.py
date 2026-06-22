from backend.app.services.document_processing.models import (
    CleanerConfig,
    CleaningOperation,
    DocumentFormat,
    ExtractedDocument,
    ExtractedMetadata,
    PageInfo,
)
from backend.app.services.document_processing.cleaners import LegalCleaner
from backend.app.services.document_processing.extractors import PDFExtractor


class TestLegalCleaner:
    def test_clean_extracted_document(self, extracted_pdf):
        cleaner = LegalCleaner()
        result = cleaner.clean(extracted_pdf)
        assert result.extracted_id == extracted_pdf.raw_id
        assert len(result.text) > 0
        assert result.stats.original_char_count > 0
        assert result.stats.cleaned_char_count > 0

    def test_no_operations_disabled(self):
        from backend.app.services.document_processing.models import ExtractedDocument, ExtractedMetadata, PageInfo
        doc = ExtractedDocument(
            raw_id="test",
            format=DocumentFormat.TXT,
            text="Hello\n\n\n\nWorld.\n",
            pages=[],
            metadata=ExtractedMetadata(word_count=2, char_count=20, extraction_strategy="test"),
        )
        config = CleanerConfig(enabled_operations=[])
        cleaner = LegalCleaner(config=config)
        result = cleaner.clean(doc)
        assert result.stats.operations_applied == []

    def test_cleaned_output_different_from_input(self, extracted_pdf):
        cleaner = LegalCleaner()
        result = cleaner.clean(extracted_pdf)
        if result.stats.operations_applied:
            assert result.text != extracted_pdf.text or len(result.text) != extracted_pdf.metadata.char_count

    def test_preserves_document_structure(self, extracted_pdf):
        cleaner = LegalCleaner()
        result = cleaner.clean(extracted_pdf)
        assert "Privacy Policy" in result.text
        assert "Introduction" in result.text
        assert "Data Collection" in result.text

    def test_multiple_operations_tracked(self, extracted_pdf):
        config = CleanerConfig()
        cleaner = LegalCleaner(config=config)
        result = cleaner.clean(extracted_pdf)
        for op in result.stats.operations_applied:
            assert isinstance(op, CleaningOperation)

    def test_supported_formats(self):
        cleaner = LegalCleaner()
        formats = cleaner.supported_formats()
        assert DocumentFormat.PDF in formats
        assert DocumentFormat.DOCX in formats
        assert DocumentFormat.TXT in formats
        assert DocumentFormat.HTML in formats

    def test_configurable_strategy_chain(self):
        config = CleanerConfig(
            enabled_operations=[
                CleaningOperation.NORMALIZE_WHITESPACE,
                CleaningOperation.NORMALIZE_UNICODE,
            ],
        )
        cleaner = LegalCleaner(config=config)
        chain = cleaner._build_strategy_chain()
        assert len(chain) == 2

    def test_end_to_end_with_pdf_extractor(self, raw_pdf):
        extractor = PDFExtractor()
        extraction = extractor.extract(raw_pdf)
        assert extraction.success

        cleaner = LegalCleaner()
        result = cleaner.clean(extraction.document)
        assert result.extracted_id == raw_pdf.id
        assert result.stats.cleaned_char_count > 0
