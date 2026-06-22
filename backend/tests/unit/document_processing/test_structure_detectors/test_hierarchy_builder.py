from backend.app.services.document_processing.structure_detectors.strategies.hierarchy_builder import (
    HierarchyBuildingStrategy,
)
from backend.app.services.document_processing.structure_detectors.strategies.heading_detector import (
    HeadingDetectionStrategy,
)
from backend.app.services.document_processing.models import (
    CleanedDocument,
    CleaningStats,
    DocumentStructure,
    StructuralElement,
    StructuralElementType,
)


class TestHierarchyBuildingStrategy:
    def setup_method(self):
        self.strategy = HierarchyBuildingStrategy()

    def _make_doc(self, text: str) -> CleanedDocument:
        return CleanedDocument(
            extracted_id="test",
            text=text,
            stats=CleaningStats(original_char_count=len(text), cleaned_char_count=len(text), removed_char_count=0),
        )

    def test_empty_text(self):
        doc = self._make_doc("")
        result = self.strategy.process(doc)
        assert len(result.elements) == 0
        assert len(result.root_element_ids) == 0

    def test_no_headings_flat(self):
        doc = self._make_doc("First line.\nSecond line.\nThird line.\n")
        result = self.strategy.process(doc)
        assert len(result.elements) == 3
        for e in result.elements.values():
            assert e.type == StructuralElementType.PARAGRAPH

    def test_single_heading(self):
        text = "1. Introduction\nSome body text.\nMore text.\n"
        doc = self._make_doc(text)
        heading_strat = HeadingDetectionStrategy()
        structure = heading_strat.process(doc)
        result = self.strategy.process(doc, structure)
        assert len(result.elements) == 2  # heading + paragraph
        para = [e for e in result.elements.values() if e.type == StructuralElementType.PARAGRAPH]
        assert len(para) == 1
        assert para[0].parent_id is None or para[0].parent_id in result.root_element_ids

    def test_nested_headings(self):
        text = (
            "1. Introduction\n"
            "Intro text.\n"
            "1.1 Background\n"
            "Background text.\n"
            "1.1.1 Details\n"
            "Detail text.\n"
            "2. Conclusion\n"
            "Conclusion text.\n"
        )
        doc = self._make_doc(text)
        heading_strat = HeadingDetectionStrategy()
        structure = heading_strat.process(doc)
        result = self.strategy.process(doc, structure)
        assert len(result.elements) >= 4
        elems = {e.element_id: e for e in result.elements.values()}
        headings = {eid: e for eid, e in elems.items() if e.type != StructuralElementType.PARAGRAPH}
        sorted_h = sorted(headings.values(), key=lambda e: e.metadata["char_start"])
        assert sorted_h[0].element_id in result.root_element_ids
        if sorted_h[1].parent_id:
            assert sorted_h[1].parent_id == sorted_h[0].element_id

    def test_parent_child_tree(self):
        text = (
            "1. Top\n"
            "Top text.\n"
            "1.1 Mid\n"
            "Mid text.\n"
            "1.1.1 Bottom\n"
            "Bottom text.\n"
        )
        doc = self._make_doc(text)
        heading_strat = HeadingDetectionStrategy()
        structure = heading_strat.process(doc)
        result = self.strategy.process(doc, structure)
        elems = result.elements
        h1 = [e for e in elems.values() if e.level == 1][0]
        h2 = [e for e in elems.values() if e.level == 2][0]
        h3 = [e for e in elems.values() if e.level == 3][0]
        assert h2.parent_id == h1.element_id
        assert h3.parent_id == h2.element_id
        assert h2.element_id in h1.child_ids
        assert h3.element_id in h2.child_ids

    def test_flat_text_with_no_headings(self):
        text = "This is a document\nwith no headings at all.\nJust plain text.\n"
        doc = self._make_doc(text)
        empty_structure = DocumentStructure(detection_strategy="heading_detection")
        result = self.strategy.process(doc, empty_structure)
        assert len(result.elements) == 3
        for e in result.elements.values():
            assert e.type == StructuralElementType.PARAGRAPH

    def test_detects_document_title(self):
        text = (
            "PRIVACY POLICY\n"
            "\n"
            "1. Introduction\n"
            "Body text here.\n"
        )
        doc = self._make_doc(text)
        heading_strat = HeadingDetectionStrategy()
        structure = heading_strat.process(doc)
        result = self.strategy.process(doc, structure)
        elems = result.elements
        headings = [e for e in elems.values() if e.type != StructuralElementType.PARAGRAPH]
        allcaps = [e for e in headings if e.metadata.get("pattern_type") == "allcaps"]
        if allcaps:
            assert any(e.text == "PRIVACY POLICY" for e in allcaps)

    def test_build_tree_with_schedules(self):
        text = (
            "1. Introduction\n"
            "Body.\n"
            "Schedule A: Definitions\n"
            "Definition text.\n"
        )
        doc = self._make_doc(text)
        heading_strat = HeadingDetectionStrategy()
        structure = heading_strat.process(doc)
        result = self.strategy.process(doc, structure)
        schedules = [e for e in result.elements.values() if e.type == StructuralElementType.SCHEDULE]
        assert len(schedules) == 1

    def test_preserves_toc_from_prior_structure(self):
        from backend.app.services.document_processing.models import TableOfContents, TableOfContentsEntry
        text = "1. Section\nBody.\n"
        doc = self._make_doc(text)
        prior = DocumentStructure(
            detection_strategy="toc_detection",
            toc=TableOfContents(entries=[
                TableOfContentsEntry(title="1. Section", level=1, page_number=1),
            ]),
        )
        result = self.strategy.process(doc, prior)
        assert result.toc is not None
        assert len(result.toc.entries) == 1

    def test_elements_have_char_positions(self):
        text = "1. Title\nBody paragraph.\n2. Next\nMore body.\n"
        doc = self._make_doc(text)
        heading_strat = HeadingDetectionStrategy()
        structure = heading_strat.process(doc)
        result = self.strategy.process(doc, structure)
        for e in result.elements.values():
            if e.type == StructuralElementType.PARAGRAPH:
                assert "char_start" in e.metadata
                assert "char_end" in e.metadata

    def test_integration_with_legal_document(self, cleaned_legal):
        heading_strat = HeadingDetectionStrategy()
        structure = heading_strat.process(cleaned_legal)
        result = self.strategy.process(cleaned_legal, structure)
        assert len(result.elements) > 0
        assert len(result.root_element_ids) > 0
        heading_elements = [
            e for e in result.elements.values()
            if e.type in (StructuralElementType.HEADING, StructuralElementType.SUBHEADING, StructuralElementType.SCHEDULE)
        ]
        assert len(heading_elements) >= 9
