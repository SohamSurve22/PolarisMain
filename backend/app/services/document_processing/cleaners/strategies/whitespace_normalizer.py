import re

from ...models import CleaningOperation, PageInfo
from .base import CleaningStrategy, CleansedResult


class WhitespaceNormalizer(CleaningStrategy):
    def __init__(self, max_consecutive_blank_lines: int = 2):
        self._max_blank = max_consecutive_blank_lines

    @property
    def operation(self) -> CleaningOperation:
        return CleaningOperation.NORMALIZE_WHITESPACE

    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        result = CleansedResult(text=text)
        stats: dict[str, int] = {}
        modified = text

        modified = modified.replace("\r\n", "\n")
        modified = modified.replace("\r", "\n")

        lines = modified.split("\n")
        cleaned_lines: list[str] = []
        trailing_spaces = 0
        leading_tabs = 0
        blank_count = 0

        for line in lines:
            stripped = line.rstrip()
            if stripped != line:
                trailing_spaces += 1
            tab_stripped = stripped.lstrip("\t")
            if tab_stripped != stripped:
                leading_tabs += 1
            tab_normalized = stripped.replace("\t", " ")
            if tab_normalized == "":
                blank_count += 1
                if blank_count <= self._max_blank:
                    cleaned_lines.append("")
                continue
            blank_count = 0
            while "  " in tab_normalized:
                tab_normalized = tab_normalized.replace("  ", " ")
            cleaned_lines.append(tab_normalized)

        modified = "\n".join(cleaned_lines)
        modified = modified.strip("\n")
        modified = modified + "\n"

        if trailing_spaces:
            stats["trailing_whitespace_lines"] = trailing_spaces
        if leading_tabs:
            stats["tabs_replaced"] = leading_tabs

        if modified != result.text:
            result.was_modified = True
            result.stats = stats

        result.text = modified
        return result
