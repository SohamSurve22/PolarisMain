from backend.app.services.document_processing.cleaners.strategies import ParagraphReconstructor


class TestParagraphReconstructor:
    def setup_method(self):
        self.strategy = ParagraphReconstructor(preserve_list_indentation=True)

    def test_merges_paragraph_lines(self):
        text = (
            "This is the first sentence of a\n"
            "paragraph. This continues the\n"
            "same paragraph.\n"
            "\n"
            "This is a new paragraph after a blank line.\n"
        )
        result = self.strategy.clean(text)
        assert result.was_modified
        assert "of a paragraph. This continues the same paragraph." in result.text
        assert "\n\n" in result.text

    def test_preserves_headings(self):
        text = (
            "1. Introduction\n"
            "This is the introduction paragraph.\n"
            "\n"
            "2. Scope\n"
            "This document applies to all users.\n"
        )
        result = self.strategy.clean(text)
        assert "1. Introduction\n" in result.text
        assert "2. Scope\n" in result.text

    def test_preserves_list_items(self):
        text = (
            "- Item one\n"
            "- Item two\n"
            "- Item three\n"
        )
        result = self.strategy.clean(text)
        assert result.text == text
        assert not result.was_modified

    def test_preserves_section_article_headings(self):
        text = (
            "Section 1\n"
            "Body text for section 1.\n"
            "\n"
            "Article 5\n"
            "Body text for article 5.\n"
        )
        result = self.strategy.clean(text)
        assert "Section 1\n" in result.text
        assert "Article 5\n" in result.text

    def test_empty_text(self):
        result = self.strategy.clean("")
        assert result.text == ""
