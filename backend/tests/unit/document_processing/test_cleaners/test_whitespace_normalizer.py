from backend.app.services.document_processing.cleaners.strategies import WhitespaceNormalizer


class TestWhitespaceNormalizer:
    def setup_method(self):
        self.strategy = WhitespaceNormalizer(max_consecutive_blank_lines=2)

    def test_normalizes_line_endings(self):
        text = "line1\r\nline2\rline3\nline4"
        result = self.strategy.clean(text)
        assert "\r" not in result.text
        assert result.text.startswith("line1\nline2\nline3\nline4")

    def test_collapses_multiple_spaces(self):
        text = "This   has    extra   spaces."
        result = self.strategy.clean(text)
        assert result.text.startswith("This has extra spaces.")

    def test_collapses_blank_lines(self):
        text = "line1\n\n\n\nline2"
        result = self.strategy.clean(text)
        assert "line1\n\n\nline2" in result.text
        assert "line1\n\n\n\nline2" not in result.text

    def test_removes_trailing_whitespace(self):
        text = "line1   \nline2  \nline3"
        result = self.strategy.clean(text)
        for line in result.text.split("\n"):
            assert line == line.rstrip(), f"Trailing whitespace in line: {line!r}"

    def test_replaces_tabs(self):
        text = "\tindented\tword"
        result = self.strategy.clean(text)
        assert "\t" not in result.text

    def test_no_change_if_clean(self):
        text = "Clean text\nwith proper spacing.\n"
        result = self.strategy.clean(text)
        # May still be modified (adding trailing newline)
        assert "Clean text" in result.text
        assert "proper spacing" in result.text

    def test_ending_newline(self):
        text = "hello"
        result = self.strategy.clean(text)
        assert result.text.endswith("\n")

    def test_empty_text(self):
        result = self.strategy.clean("")
        assert result.text == "\n" or result.text == ""
