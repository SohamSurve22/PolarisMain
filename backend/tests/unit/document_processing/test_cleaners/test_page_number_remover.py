from backend.app.services.document_processing.models import PageInfo
from backend.app.services.document_processing.cleaners.strategies import PageNumberRemover


class TestPageNumberRemover:
    def setup_method(self):
        self.strategy = PageNumberRemover()

    def test_removes_standalone_page_number_with_pages(self):
        pages = [
            PageInfo(page_number=1, text="Intro text\n1", char_count=14),
            PageInfo(page_number=2, text="More text\n2", char_count=12),
        ]
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert result.was_modified
        assert "1" not in result.text
        assert "Intro text" in result.text
        assert "More text" in result.text

    def test_no_page_numbers_without_pages(self):
        text = "First line\nSecond line\nThird line"
        result = self.strategy.clean(text, pages=None)
        assert not result.was_modified
        assert result.text == text

    def test_removes_page_x_format(self):
        pages = [
            PageInfo(page_number=1, text="Intro\nPage 1", char_count=11),
            PageInfo(page_number=2, text="Body\nPage 2", char_count=10),
        ]
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert result.was_modified
        assert "Page 1" not in result.text
        assert "Page 2" not in result.text

    def test_removes_dash_wrapped_numbers(self):
        pages = [
            PageInfo(page_number=1, text="Text\n- 1 -", char_count=10),
            PageInfo(page_number=2, text="More\n- 2 -", char_count=10),
        ]
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert result.was_modified
        assert "- 1 -" not in result.text

    def test_keeps_numbers_in_body(self):
        pages = [
            PageInfo(page_number=1, text="Section 1\nBody content", char_count=21),
            PageInfo(page_number=2, text="Section 2\nMore text", char_count=17),
        ]
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert not result.was_modified
        assert "Section 1" in result.text

    def test_removes_p_dot_format(self):
        pages = [
            PageInfo(page_number=1, text="Intro\np. 1", char_count=10),
            PageInfo(page_number=2, text="Body\np. 2", char_count=9),
        ]
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert result.was_modified
