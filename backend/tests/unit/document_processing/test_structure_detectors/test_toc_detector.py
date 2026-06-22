from backend.app.services.document_processing.structure_detectors.strategies.toc_detector import (
    TOCDetectionStrategy,
)
from backend.app.services.document_processing.models import (
    CleanedDocument,
    CleaningStats,
    DocumentStructure,
)


class TestTOCDetectionStrategy:
    def setup_method(self):
        self.strategy = TOCDetectionStrategy(max_lines_to_scan=50, min_entries=3)

    def _make_doc(self, text: str) -> CleanedDocument:
        return CleanedDocument(
            extracted_id="test",
            text=text,
            stats=CleaningStats(original_char_count=len(text), cleaned_char_count=len(text), removed_char_count=0),
        )

    def test_detects_toc_with_dot_leaders(self):
        text = (
            "TABLE OF CONTENTS\n"
            "1. Introduction ............. 1\n"
            "2. Scope .................... 2\n"
            "3. Definitions ............. 3\n"
            "\n"
            "1. Introduction\n"
            "Body text.\n"
        )
        doc = self._make_doc(text)
        result = self.strategy.process(doc)
        assert result.toc is not None
        assert len(result.toc.entries) >= 3
        assert result.toc.entries[0].title == "Introduction"
        assert result.toc.entries[0].page_number == 1
        assert result.toc.entries[0].level == 1

    def test_detects_toc_without_dot_leaders(self):
        text = (
            "CONTENTS\n"
            "1. Introduction    1\n"
            "2. Scope           2\n"
            "3. Definitions     3\n"
            "4. Data Processing 4\n"
        )
        doc = self._make_doc(text)
        result = self.strategy.process(doc)
        assert result.toc is not None
        assert len(result.toc.entries) >= 3

    def test_no_toc_in_short_text(self):
        doc = self._make_doc("Just a short document.\nNo table of contents here.\n")
        result = self.strategy.process(doc)
        assert result.toc is None

    def test_no_toc_with_too_few_entries(self):
        strategy = TOCDetectionStrategy(max_lines_to_scan=50, min_entries=5)
        text = (
            "1. Title 1\n"
            "2. Title 2\n"
            "3. Title 3\n"
        )
        doc = self._make_doc(text)
        result = strategy.process(doc)
        assert result.toc is None

    def test_preserves_existing_structure(self):
        text = "1. Introduction ..... 1\n2. Scope ..... 2\n3. Details ..... 3\n"
        doc = self._make_doc(text)
        prior = DocumentStructure(detection_strategy="some_prior")
        prior.elements["h_1"] = prior.elements.get("h_1", None)
        result = self.strategy.process(doc, prior)
        assert result.detection_strategy == "some_prior"
        assert result.toc is not None

    def test_skips_duplicate_titles(self):
        text = (
            "1. Introduction ..... 1\n"
            "1. Introduction ..... 1\n"
            "2. Scope ..... 2\n"
            "2. Scope ..... 2\n"
            "3. Details ..... 3\n"
        )
        doc = self._make_doc(text)
        result = self.strategy.process(doc)
        assert result.toc is not None
        titles = [e.title for e in result.toc.entries]
        assert len(titles) == len(set(titles))

    def test_empty_text(self):
        doc = self._make_doc("")
        result = self.strategy.process(doc)
        assert result.toc is None

    def test_handles_multi_level_toc(self):
        text = (
            "1. Overview 1\n"
            "1.1 Background 2\n"
            "1.2 Purpose 3\n"
            "2. Scope 4\n"
            "2.1 Limitations 5\n"
        )
        doc = self._make_doc(text)
        result = self.strategy.process(doc)
        assert result.toc is not None
        assert len(result.toc.entries) >= 3
        entry_1_1 = [e for e in result.toc.entries if e.title == "Background"][0]
        assert entry_1_1.level == 2
