from backend.app.services.document_processing.models import PageInfo
from backend.app.services.document_processing.cleaners.strategies import HeaderFooterRemover


class TestHeaderFooterRemover:
    def setup_method(self):
        self.strategy = HeaderFooterRemover(min_pages=3, match_threshold=0.5)

    def _make_pages(self, headers, bodies, footers):
        pages = []
        for i, (h, b, f) in enumerate(zip(headers, bodies, footers)):
            text = f"{h}\n{b}\n{f}" if f else f"{h}\n{b}"
            pages.append(PageInfo(page_number=i + 1, text=text, char_count=len(text)))
        return pages

    def test_removes_repeated_header(self):
        pages = self._make_pages(
            headers=["Header"] * 5,
            bodies=["Body text paragraph " + str(i) for i in range(5)],
            footers=[""] * 5,
        )
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert result.was_modified
        assert "Header" not in result.text

    def test_removes_repeated_footer(self):
        pages = self._make_pages(
            headers=[""] * 5,
            bodies=["Body text " + str(i) for i in range(5)],
            footers=["© Company Name"] * 5,
        )
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert result.was_modified
        assert "© Company Name" not in result.text

    def test_skips_short_texts(self):
        pages = self._make_pages(
            headers=["A"] * 5,
            bodies=["B"] * 5,
            footers=["C"] * 5,
        )
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert not result.was_modified

    def test_not_enough_pages(self):
        pages = self._make_pages(
            headers=["H"] * 2,
            bodies=["B"] * 2,
            footers=["F"] * 2,
        )
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert not result.was_modified

    def test_no_pages(self):
        text = "Just some text."
        result = self.strategy.clean(text, pages=None)
        assert not result.was_modified
        assert result.text == text

    def test_no_modification_without_repetition(self):
        pages = self._make_pages(
            headers=["H1", "H2", "H3", "H4", "H5"],
            bodies=["B"] * 5,
            footers=["F1", "F2", "F3", "F4", "F5"],
        )
        text = "\n\n".join(p.text for p in pages)
        result = self.strategy.clean(text, pages)
        assert not result.was_modified
