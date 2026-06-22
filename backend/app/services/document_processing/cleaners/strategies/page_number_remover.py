import re

from ...models import CleaningOperation, PageInfo
from .base import CleaningStrategy, CleansedResult


_PAGE_NUMBER_PATTERNS = [
    re.compile(r"^\s*-?\s*\d+\s*-?\s*$"),
    re.compile(r"^\s*Page\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
    re.compile(r"^\s*\d+\s*of\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*p\.?\s*\d+\s*$", re.IGNORECASE),
]


class PageNumberRemover(CleaningStrategy):
    @property
    def operation(self) -> CleaningOperation:
        return CleaningOperation.REMOVE_PAGE_NUMBERS

    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        result = CleansedResult(text=text)

        if not pages:
            lines = text.split("\n")
            filtered: list[str] = []
            removed = 0
            for line in lines:
                if any(p.match(line) for p in _PAGE_NUMBER_PATTERNS):
                    removed += 1
                    continue
                filtered.append(line)
            result.text = "\n".join(filtered)
            if removed:
                result.was_modified = True
                result.stats["page_numbers_removed"] = removed
            return result

        cleaned_pages: list[str] = []
        total_removed = 0

        for page in pages:
            lines = page.text.split("\n")
            filtered = self._remove_from_lines(lines)
            removed_count = len(lines) - len(filtered)
            total_removed += removed_count
            cleaned_pages.append("\n".join(filtered))

        result.text = "\n\n".join(cleaned_pages)
        if total_removed:
            result.was_modified = True
            result.stats["page_numbers_removed"] = total_removed
        return result

    def _remove_from_lines(self, lines: list[str]) -> list[str]:
        if not lines:
            return lines

        result_lines = list(lines)
        if result_lines and any(p.match(result_lines[0]) for p in _PAGE_NUMBER_PATTERNS):
            result_lines.pop(0)
        if len(result_lines) >= 1 and any(p.match(result_lines[-1]) for p in _PAGE_NUMBER_PATTERNS):
            result_lines.pop(-1)
        return result_lines
