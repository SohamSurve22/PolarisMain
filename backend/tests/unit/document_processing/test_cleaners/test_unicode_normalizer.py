from backend.app.services.document_processing.cleaners.strategies import UnicodeNormalizer


class TestUnicodeNormalizer:
    def setup_method(self):
        self.strategy = UnicodeNormalizer()

    def test_nfc_normalization(self):
        text = "\u00e9clair"  # é as single code point
        result = self.strategy.clean(text)
        assert result.text == text
        assert not result.was_modified

    def test_fixes_ligatures(self):
        text = "This ﬁle contains ﬁ ligatures like ﬁ, ﬂ, ﬃ."
        result = self.strategy.clean(text)
        assert "fi" in result.text
        assert "fl" in result.text
        assert "ffi" in result.text
        assert "\ufb01" not in result.text
        assert result.was_modified
        assert result.stats["ligatures_fixed"] >= 3

    def test_no_ligatures_unchanged(self):
        text = "Simple text without ligatures."
        result = self.strategy.clean(text)
        assert result.text == text
        assert not result.was_modified

    def test_normalizes_dashes(self):
        text = "en dash \u2013 is replaced"
        result = self.strategy.clean(text)
        assert "\u2013" not in result.text
        assert "\u2014" in result.text

    def test_normalizes_ellipsis(self):
        text = "And so on\u2026"
        result = self.strategy.clean(text)
        assert "\u2026" not in result.text
        assert "..." in result.text

    def test_empty_text(self):
        result = self.strategy.clean("")
        assert result.text == ""
        assert not result.was_modified

    def test_pages_parameter_ignored(self):
        text = "Test with pages."
        result = self.strategy.clean(text, pages=[])
        assert result.text == text
