from backend.app.services.document_processing.structure_detectors import StructureDetector
from backend.app.services.document_processing.models import (
    StructureDetectorConfig,
    StructuralElementType,
)


class TestStructureDetector:
    def test_detect_legal_document(self, cleaned_legal):
        detector = StructureDetector()
        result = detector.detect(cleaned_legal)
        assert result.cleaned_id == cleaned_legal.extracted_id
        assert result.structure is not None
        assert len(result.structure.root_element_ids) > 0
        assert len(result.structure.elements) > 0

    def test_supported_formats(self):
        detector = StructureDetector()
        formats = detector.supported_formats()
        assert len(formats) == 4

    def test_empty_document(self, cleaned_empty):
        detector = StructureDetector()
        result = detector.detect(cleaned_empty)
        assert result.cleaned_id == cleaned_empty.extracted_id
        assert len(result.structure.elements) == 0

    def test_heading_types_found(self, cleaned_legal):
        detector = StructureDetector()
        result = detector.detect(cleaned_legal)
        types_found = {e.type for e in result.structure.elements.values()}
        assert StructuralElementType.HEADING in types_found
        assert StructuralElementType.SUBHEADING in types_found

    def test_hierarchy_structure(self, cleaned_legal):
        detector = StructureDetector()
        result = detector.detect(cleaned_legal)
        root_elements = [result.structure.elements[eid] for eid in result.structure.root_element_ids]
        for root in root_elements:
            assert root.parent_id is None

    def test_flat_document(self, cleaned_flat):
        detector = StructureDetector()
        result = detector.detect(cleaned_flat)
        assert len(result.structure.elements) > 0
        for e in result.structure.elements.values():
            assert e.type == StructuralElementType.PARAGRAPH

    def test_with_config_disabling_toc(self, cleaned_legal):
        config = StructureDetectorConfig(enable_toc_detection=False)
        detector = StructureDetector(config=config)
        result = detector.detect(cleaned_legal)
        assert result.structure.toc is None

    def test_custom_patterns_in_config(self, cleaned_legal):
        config = StructureDetectorConfig(heading_patterns=[r"^CHAPTER\s+\d+"])
        detector = StructureDetector(config=config)
        result = detector.detect(cleaned_legal)
        assert result.cleaned_id == cleaned_legal.extracted_id

    def test_min_confidence_config(self):
        from backend.app.services.document_processing.models import CleanedDocument, CleaningStats
        text = "PRIVACY POLICY\nLow confidence allcaps.\n1. Real heading\nBody.\n"
        doc = CleanedDocument(
            extracted_id="test",
            text=text,
            stats=CleaningStats(original_char_count=len(text), cleaned_char_count=len(text), removed_char_count=0),
        )
        config = StructureDetectorConfig(min_heading_confidence=0.9)
        detector = StructureDetector(config=config)
        result = detector.detect(doc)
        heading_texts = [e.text for e in result.structure.elements.values()
                         if e.type == StructuralElementType.HEADING]
        assert "PRIVACY POLICY" not in heading_texts
        assert "1. Real heading" in heading_texts

    def test_detect_returns_all_sections(self, cleaned_legal):
        detector = StructureDetector()
        result = detector.detect(cleaned_legal)
        elems = result.structure.elements
        heading_texts = [e.text for e in elems.values() if e.type != StructuralElementType.PARAGRAPH]
        assert "1. Introduction" in heading_texts
        assert "1.1 Information We Collect" in heading_texts
        assert "1.1.1 Account Information" in heading_texts
        assert "Article 4: Legal Basis" in heading_texts
        assert "Schedule A: Definitions" in heading_texts

    def test_paragraphs_between_headings(self, cleaned_legal):
        detector = StructureDetector()
        result = detector.detect(cleaned_legal)
        paragraphs = [e for e in result.structure.elements.values()
                      if e.type == StructuralElementType.PARAGRAPH]
        assert len(paragraphs) > 0
        for p in paragraphs:
            assert len(p.text) > 0
