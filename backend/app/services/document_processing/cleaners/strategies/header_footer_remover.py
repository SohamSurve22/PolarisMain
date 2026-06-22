import re
from collections import Counter

from ...models import CleaningOperation, PageInfo
from .base import CleaningStrategy, CleansedResult


class HeaderFooterRemover(CleaningStrategy):
    def __init__(
        self,
        min_pages: int = 3,
        match_threshold: float = 0.5,
        lines_to_check: int = 2,
    ):
        self._min_pages = min_pages
        self._threshold = match_threshold
        self._lines_to_check = lines_to_check

    @property
    def operation(self) -> CleaningOperation:
        return CleaningOperation.REMOVE_HEADERS

    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        result = CleansedResult(text=text)
        if not pages or len(pages) < self._min_pages:
            return result

        page_texts = [p.text for p in pages]
        if not any(pt.strip() for pt in page_texts):
            return result

        header_candidates: list[str] = []
        footer_candidates: list[str] = []

        for pt in page_texts:
            lines = pt.split("\n")
            for i in range(min(self._lines_to_check, len(lines))):
                header_candidates.append(lines[i].strip())
            for i in range(max(0, len(lines) - self._lines_to_check), len(lines)):
                footer_candidates.append(lines[i].strip())

        total_pages = len(page_texts)
        header_threshold = max(1, int(total_pages * self._threshold))
        footer_threshold = max(1, int(total_pages * self._threshold))

        header_counts = Counter(header_candidates)
        footer_counts = Counter(footer_candidates)

        headers_to_remove: set[str] = set()
        footers_to_remove: set[str] = set()

        for candidate, count in header_counts.items():
            if not candidate:
                continue
            if len(candidate) < 3:
                continue
            if count >= header_threshold:
                headers_to_remove.add(candidate)

        for candidate, count in footer_counts.items():
            if not candidate:
                continue
            if len(candidate) < 3:
                continue
            if count >= footer_threshold:
                footers_to_remove.add(candidate)

        if not headers_to_remove and not footers_to_remove:
            return result

        removed_lines = 0
        cleaned_pages: list[str] = []

        for pt in page_texts:
            lines = pt.split("\n")
            filtered: list[str] = []
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped in headers_to_remove and i < self._lines_to_check:
                    removed_lines += 1
                    continue
                if stripped in footers_to_remove and i >= len(lines) - self._lines_to_check:
                    removed_lines += 1
                    continue
                filtered.append(line)
            cleaned_pages.append("\n".join(filtered))

        result.text = "\n\n".join(cleaned_pages)
        result.was_modified = removed_lines > 0
        result.stats["headers_removed"] = len(headers_to_remove)
        result.stats["footers_removed"] = len(footers_to_remove)
        result.stats["total_lines_removed"] = removed_lines
        return result
