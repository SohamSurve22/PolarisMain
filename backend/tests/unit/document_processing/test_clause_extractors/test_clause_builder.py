from backend.app.services.document_processing.clause_extractors.strategies.clause_builder import (
    ClauseBuilderStrategy,
)
from backend.app.services.document_processing.models import (
    StructuralElementType,
)


class TestClauseBuilderStrategy:
    def setup_method(self):
        self.strategy = ClauseBuilderStrategy()

    def test_extracts_from_simple_document(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        assert result.clause_count > 0
        assert len(result.root_clause_ids) > 0

    def test_creates_heading_clauses(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        heading_clauses = [c for c in result.clauses.values() if c.metadata.get("type") == "heading"]
        assert len(heading_clauses) >= 3
        assert any("Introduction" in c.body for c in heading_clauses)
        assert any("Data Collection" in c.body for c in heading_clauses)
        assert any("Rights" in c.body for c in heading_clauses)

    def test_heading_clauses_have_confidence_one(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        for c in result.clauses.values():
            if c.metadata.get("type") == "heading":
                assert c.confidence == 1.0

    def test_detects_list_items_as_clauses(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        list_clauses = [c for c in result.clauses.values() if c.metadata.get("type") == "list_item"]
        assert len(list_clauses) >= 3
        texts = [c.body for c in list_clauses]
        assert "Name and contact information" in texts
        assert "Financial information" in texts
        assert "Usage data" in texts

    def test_list_item_clauses_have_clause_numbers(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        list_clauses = [c for c in result.clauses.values() if c.metadata.get("type") == "list_item"]
        for c in list_clauses:
            assert c.clause_number is not None
            assert c.clause_number in ("(a)", "(b)", "(c)")

    def test_splits_multi_sentence_paragraphs(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        sentence_clauses = [c for c in result.clauses.values() if c.metadata.get("type") == "sentence"]
        assert len(sentence_clauses) >= 2

    def test_paragraph_clause_has_section_heading(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        para_clauses = [c for c in result.clauses.values() if c.metadata.get("type") in ("paragraph", "list_item", "sentence")]
        for c in para_clauses:
            assert c.heading is not None

    def test_tracks_char_offsets(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        for c in result.clauses.values():
            assert "char_start" in c.metadata
            assert "char_end" in c.metadata
            assert c.metadata["char_end"] >= c.metadata["char_start"]

    def test_tracks_order(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        orders = [c.metadata["order"] for c in result.clauses.values()]
        assert orders == sorted(orders)

    def test_empty_document(self):
        from backend.app.services.document_processing.models import (
            CleanedDocument,
            CleaningStats,
            DocumentStructure,
            StructuredDocument,
        )
        doc = CleanedDocument(
            extracted_id="empty",
            text="",
            stats=CleaningStats(original_char_count=0, cleaned_char_count=0, removed_char_count=0),
        )
        struct = StructuredDocument(
            cleaned_id="empty",
            structure=DocumentStructure(detection_strategy="empty"),
        )
        result = self.strategy.process(doc, struct)
        assert result.clause_count == 0
        assert len(result.root_clause_ids) == 0

    def test_nested_list_hierarchy(self, cleaned_nested, structured_doc_nested):
        result = self.strategy.process(cleaned_nested, structured_doc_nested)
        list_clauses = [c for c in result.clauses.values() if c.metadata.get("type") == "list_item"]
        assert len(list_clauses) == 2  # (a) Users, (b) Partners

    def test_heading_clause_has_element_ids(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        for c in result.clauses.values():
            if c.metadata.get("type") == "heading":
                assert len(c.element_ids) == 1
                assert c.element_ids[0].startswith("h_")

    def test_all_clauses_have_unique_ids(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        ids = [c.clause_id for c in result.clauses.values()]
        assert len(ids) == len(set(ids))

    def test_parent_child_relationships(self, cleaned_doc, structured_doc):
        result = self.strategy.process(cleaned_doc, structured_doc)
        for c in result.clauses.values():
            if c.parent_clause_id is not None:
                assert c.parent_clause_id in result.clauses
            for child_id in c.child_clause_ids:
                assert child_id in result.clauses
                assert result.clauses[child_id].parent_clause_id == c.clause_id

    def test_nested_heading_hierarchy(self, cleaned_nested, structured_doc_nested):
        result = self.strategy.process(cleaned_nested, structured_doc_nested)
        h1_clauses = [c for c in result.clauses.values() if "General" in c.body]
        assert len(h1_clauses) == 1
        h1 = h1_clauses[0]
        children = [result.clauses[cid] for cid in h1.child_clause_ids]
        child_texts = [c.body for c in children]
        assert any("Scope" in t for t in child_texts)
        assert any("Definitions" in t for t in child_texts)
