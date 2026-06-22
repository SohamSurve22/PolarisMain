from backend.app.services.document_processing.cleaners.strategies import QuotationNormalizer


class TestQuotationNormalizer:
    def setup_method(self):
        self.strategy = QuotationNormalizer()

    def test_normalizes_double_quotes(self):
        text = "He said \u201cHello world\u201d."
        result = self.strategy.clean(text)
        assert result.was_modified
        assert '"Hello world"' in result.text

    def test_normalizes_single_quotes(self):
        text = "It\u2019s a test."
        result = self.strategy.clean(text)
        assert result.was_modified
        assert "It's" in result.text

    def test_normalizes_guillemets(self):
        text = "\u00abQuote\u00bb"
        result = self.strategy.clean(text)
        assert '"Quote"' in result.text

    def test_normalizes_long_dashes(self):
        text = "This\u2014is an em dash."
        result = self.strategy.clean(text)
        assert "This\u2014is" in result.text

    def test_no_change_for_ascii_text(self):
        text = 'Simple "quoted" text.'
        result = self.strategy.clean(text)
        assert not result.was_modified
        assert result.text == text

    def test_empty_text(self):
        result = self.strategy.clean("")
        assert result.text == ""
        assert not result.was_modified
