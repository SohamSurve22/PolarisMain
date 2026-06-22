from backend.app.services.document_processing.structure_detectors.strategies.heading_detector import (
    HeadingDetectionStrategy,
)
from backend.app.services.document_processing.models import (
    CleanedDocument,
    CleaningStats,
    DocumentStructure,
    StructuralElementType,
)


class TestHeadingDetectionStrategy:
    def setup_method(self):
        self.strategy = HeadingDetectionStrategy(min_confidence=0.5)

    def _make_doc(self, text: str) -> CleanedDocument:
        return CleanedDocument(
            extracted_id="test",
            text=text,
            stats=CleaningStats(original_char_count=len(text), cleaned_char_count=len(text), removed_char_count=0),
        )

    def test_detects_decimal_1_headings(self):
        doc = self._make_doc("1. Introduction\nSome body text here.\n2. Scope\nMore text.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        headings = sorted(result.elements.values(), key=lambda e: e.metadata["char_start"])
        assert headings[0].text == "1. Introduction"
        assert headings[0].level == 1
        assert headings[0].type == StructuralElementType.HEADING
        assert headings[1].text == "2. Scope"
        assert headings[1].level == 1

    def test_detects_decimal_2_headings(self):
        doc = self._make_doc("1.1 Background\nSome text.\n1.2 Purpose\nMore text.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        h1, h2 = sorted(result.elements.values(), key=lambda e: e.metadata["char_start"])
        assert h1.level == 2
        assert h1.type == StructuralElementType.SUBHEADING
        assert h2.level == 2

    def test_detects_decimal_3_headings(self):
        doc = self._make_doc("1.1.1 Details\nFine print here.\n2.1.1 Exception\nException details.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        for e in result.elements.values():
            assert e.level == 3

    def test_mixed_decimal_levels(self):
        text = (
            "1. Introduction\n"
            "Body text.\n"
            "1.1 Background\n"
            "More body.\n"
            "1.1.1 Details\n"
            "Even more.\n"
            "2. Conclusion\n"
            "Final body.\n"
        )
        doc = self._make_doc(text)
        result = self.strategy.process(doc)
        assert len(result.elements) == 4
        elems = sorted(result.elements.values(), key=lambda e: e.metadata["char_start"])
        assert [(e.level, e.type) for e in elems] == [
            (1, StructuralElementType.HEADING),
            (2, StructuralElementType.SUBHEADING),
            (3, StructuralElementType.SUBHEADING),
            (1, StructuralElementType.HEADING),
        ]

    def test_detects_named_headings(self):
        doc = self._make_doc("Article 1: Scope\nBody.\nSection 2.1: Details\nMore.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        h1, h2 = sorted(result.elements.values(), key=lambda e: e.metadata["char_start"])
        assert h1.level == 1
        assert h2.level == 2

    def test_detects_division_markers(self):
        doc = self._make_doc("Schedule A: Definitions\nTerms defined.\nAppendix B\nMore terms.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        for e in result.elements.values():
            assert e.level == 0
            assert e.type == StructuralElementType.SCHEDULE

    def test_detects_roman_numeral_headings(self):
        doc = self._make_doc("I. General Provisions\nText.\nII. Specific Provisions\nMore text.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        for e in result.elements.values():
            assert e.level == 1

    def test_detects_alpha_headings(self):
        doc = self._make_doc("A. First Section\nBody.\nB. Second Section\nMore.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        for e in result.elements.values():
            assert e.level == 2

    def test_detects_allcaps_headings(self):
        doc = self._make_doc("PRIVACY POLICY\nBody text here.\nTERMS OF USE\nMore body text.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        for e in result.elements.values():
            assert e.level == 1
            assert e.type == StructuralElementType.HEADING

    def test_skips_empty_text(self):
        doc = self._make_doc("")
        result = self.strategy.process(doc)
        assert len(result.elements) == 0

    def test_skips_whitespace_only(self):
        doc = self._make_doc("   \n\n  \n")
        result = self.strategy.process(doc)
        assert len(result.elements) == 0

    def test_no_heading_in_plain_text(self):
        doc = self._make_doc("This is just a plain paragraph with no headings.")
        result = self.strategy.process(doc)
        assert len(result.elements) == 0

    def test_tracks_char_positions(self):
        doc = self._make_doc("Preamble text.\n1. Introduction\nBody.\n")
        result = self.strategy.process(doc)
        assert len(result.elements) == 1
        h = list(result.elements.values())[0]
        assert h.metadata["char_start"] == 15
        assert h.metadata["char_end"] == 30

    def test_tracks_line_numbers(self):
        doc = self._make_doc("Line 1\n1. Introduction\nLine 3\n2. Scope\n")
        result = self.strategy.process(doc)
        assert len(result.elements) == 2
        elems = sorted(result.elements.values(), key=lambda e: e.metadata["char_start"])
        assert elems[0].metadata["line_number"] == 2
        assert elems[1].metadata["line_number"] == 4

    def test_custom_patterns(self):
        strategy = HeadingDetectionStrategy(min_confidence=0.5, custom_patterns=[r"^CHAPTER\s+\d+\b"])
        doc = self._make_doc("CHAPTER 1\nBody.\nCHAPTER 2\nMore.")
        result = strategy.process(doc)
        assert len(result.elements) == 2

    def test_confidence_threshold_filters(self):
        strategy = HeadingDetectionStrategy(min_confidence=0.9)
        doc = self._make_doc("PRIVACY POLICY\nAll caps heading.\n1. Real heading\nBody.")
        result = strategy.process(doc)
        assert len(result.elements) == 1
        assert result.elements["h_1"].text == "1. Real heading"

    def test_combined_document_structure(self):
        text = (
            "PRIVACY POLICY\n"
            "\n"
            "1. Introduction\n"
            "Body text.\n"
            "1.1 Background\n"
            "More body.\n"
            "Article 2: Scope\n"
            "Scope text.\n"
            "Schedule A: Definitions\n"
            "Definition text.\n"
        )
        doc = self._make_doc(text)
        result = self.strategy.process(doc)
        assert len(result.elements) == 5
        type_count = {}
        for e in result.elements.values():
            type_count[e.type] = type_count.get(e.type, 0) + 1
        assert type_count[StructuralElementType.HEADING] == 3
        assert type_count[StructuralElementType.SUBHEADING] == 1
        assert type_count[StructuralElementType.SCHEDULE] == 1
