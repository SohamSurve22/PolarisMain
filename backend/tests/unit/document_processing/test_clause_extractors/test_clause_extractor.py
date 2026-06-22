from backend.app.services.document_processing.clause_extractors import ClauseExtractor
from backend.app.services.document_processing.models import (
    ClauseExtractorConfig,
)


class TestClauseExtractor:
    def test_extract_simple_document(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        assert result.structured_id == cleaned_doc.extracted_id
        assert result.clause_count > 0
        assert len(result.root_clause_ids) > 0

    def test_supported_formats(self):
        extractor = ClauseExtractor()
        formats = extractor.supported_formats()
        assert len(formats) == 4

    def test_empty_document(self, empty_cleaned, empty_structured):
        extractor = ClauseExtractor()
        result = extractor.extract(empty_cleaned, empty_structured)
        assert result.clause_count == 0
        assert len(result.root_clause_ids) == 0

    def test_extraction_strategy(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        assert result.extraction_strategy == "hierarchical"

    def test_with_confidence_config(self, cleaned_doc, structured_doc):
        config = ClauseExtractorConfig(min_clause_confidence=0.3, max_clause_depth=5)
        extractor = ClauseExtractor(config=config)
        result = extractor.extract(cleaned_doc, structured_doc)
        assert result.clause_count > 0

    def test_integration_with_structure_detector(self):
        from backend.app.services.document_processing.models import (
            CleanedDocument,
            CleaningStats,
        )
        from backend.app.services.document_processing.structure_detectors import StructureDetector

        text = (
            "1. Scope\n"
            "This policy applies to all users. It covers data processing.\n"
            "(a) Collection\n"
            "(b) Storage\n"
            "2. Rights\n"
            "You have the right to access.\n"
        )
        cleaned = CleanedDocument(
            extracted_id="test-int",
            text=text,
            stats=CleaningStats(original_char_count=len(text), cleaned_char_count=len(text), removed_char_count=0),
        )
        structure_detector = StructureDetector()
        structured_doc = structure_detector.detect(cleaned)

        extractor = ClauseExtractor()
        result = extractor.extract(cleaned, structured_doc)
        assert result.clause_count > 0
        assert len(result.root_clause_ids) > 0

        all_texts = [c.body for c in result.clauses.values()]
        assert "Scope" in " ".join(all_texts)
        assert "Rights" in " ".join(all_texts)

    def test_clauses_have_all_required_fields(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        for c in result.clauses.values():
            assert c.clause_id
            assert c.body
            assert c.level >= 0
            assert 0.0 <= c.confidence <= 1.0
            assert "char_start" in c.metadata
            assert "char_end" in c.metadata
            assert "order" in c.metadata

    def test_root_clauses_are_top_level(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        for root_id in result.root_clause_ids:
            assert root_id in result.clauses
            assert result.clauses[root_id].parent_clause_id is None

    def test_clause_order_is_sequential(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        orders = sorted([c.metadata["order"] for c in result.clauses.values()])
        expected = list(range(1, len(orders) + 1))
        assert orders == expected

    def test_all_list_items_become_clauses(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        list_bodies = [c.body for c in result.clauses.values()
                       if c.metadata.get("type") == "list_item"]
        assert "Name and contact information" in list_bodies
        assert "Financial information" in list_bodies
        assert "Usage data" in list_bodies

    def test_multi_sentence_paragraph_split(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        sentence_bodies = [c.body for c in result.clauses.values()
                           if c.metadata.get("type") == "sentence"]
        rights_sentences = [s for s in sentence_bodies if "right" in s.lower()]
        assert len(rights_sentences) >= 2

    def test_confidence_levels(self, cleaned_doc, structured_doc):
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned_doc, structured_doc)
        for c in result.clauses.values():
            ctype = c.metadata.get("type", "")
            if ctype == "heading":
                assert c.confidence == 1.0
            elif ctype == "list_item":
                assert c.confidence == 0.95
            elif ctype == "sentence":
                assert c.confidence == 0.7
            elif ctype == "paragraph":
                assert c.confidence == 0.9

    def test_end_to_end_with_legal_terms(self):
        from backend.app.services.document_processing.models import (
            CleanedDocument,
            CleaningStats,
        )
        from backend.app.services.document_processing.structure_detectors import StructureDetector

        text = (
            "1. Acceptance\n"
            "By using this service you agree to these terms. You must be 18 or older.\n"
            "(a) You must provide accurate information.\n"
            "(b) You must maintain confidentiality.\n"
            "2. Termination\n"
            "We may terminate your access. We will notify you in writing.\n"
        )
        cleaned = CleanedDocument(
            extracted_id="test-terms",
            text=text,
            stats=CleaningStats(original_char_count=len(text), cleaned_char_count=len(text), removed_char_count=0),
        )
        structure = StructureDetector().detect(cleaned)
        extractor = ClauseExtractor()
        result = extractor.extract(cleaned, structure)
        assert result.clause_count > 0
        bodies = [c.body for c in result.clauses.values()]
        assert any("Acceptance" in b for b in bodies)
        assert any("Termination" in b for b in bodies)
