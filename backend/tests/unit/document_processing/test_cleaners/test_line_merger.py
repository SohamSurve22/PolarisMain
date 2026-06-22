from backend.app.services.document_processing.cleaners.strategies import LineMerger


class TestLineMerger:
    def setup_method(self):
        self.strategy = LineMerger(merge_hyphenated=True, merge_continuation=True)

    def test_merges_hyphenated_words(self):
        text = "This is a hyphen-\nated word."
        result = self.strategy.clean(text)
        assert result.was_modified
        assert "hyphen-\nated" not in result.text
        assert "hyphenated" in result.text

    def test_merges_continuation_lines(self):
        text = (
            "The Data Protection Officer is responsible for\n"
            "overseeing compliance with this policy and\n"
            "any related data protection laws.\n"
        )
        result = self.strategy.clean(text)
        assert result.was_modified
        assert "for overseeing" in result.text

    def test_no_hyphenated_merge_when_disabled(self):
        strategy = LineMerger(merge_hyphenated=False, merge_continuation=True)
        text = "This is a hyphen-\nated word."
        result = strategy.clean(text)
        assert "hyphen-\nated" in result.text

    def test_keeps_short_lines_intact(self):
        text = "- List item 1\n- List item 2"
        result = self.strategy.clean(text)
        assert "- List item 1" in result.text
        assert "- List item 2" in result.text

    def test_no_change_for_normal_text(self):
        text = "Normal paragraph text.\n\nAnother paragraph."
        result = self.strategy.clean(text)
        assert not result.was_modified

    def test_empty_text(self):
        result = self.strategy.clean("")
        assert result.text == ""
        assert not result.was_modified
