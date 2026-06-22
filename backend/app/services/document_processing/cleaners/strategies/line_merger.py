import re

from ...models import CleaningOperation, PageInfo
from .base import CleaningStrategy, CleansedResult


_HYPHENATED_BREAK_RE = re.compile(r"(\w+)-\s*\n\s*(\w+)")
_CONTINUATION_RE = re.compile(r"^([a-z0-9])")


class LineMerger(CleaningStrategy):
    def __init__(
        self,
        merge_hyphenated: bool = True,
        merge_continuation: bool = True,
    ):
        self._merge_hyphenated = merge_hyphenated
        self._merge_continuation = merge_continuation

    @property
    def operation(self) -> CleaningOperation:
        return CleaningOperation.MERGE_LINES

    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        result = CleansedResult(text=text)
        stats: dict[str, int] = {}

        modified = text

        if self._merge_hyphenated:
            before = modified
            modified = _HYPHENATED_BREAK_RE.sub(r"\1\2", modified)
            hyphenated = sum(1 for _ in _HYPHENATED_BREAK_RE.finditer(before))
            if hyphenated:
                stats["hyphenated_words_merged"] = hyphenated

        if self._merge_continuation:
            lines = modified.split("\n")
            merged: list[str] = []
            continuation_count = 0
            i = 0
            while i < len(lines):
                current = lines[i]
                if (
                    current
                    and i + 1 < len(lines)
                    and lines[i + 1]
                    and current[-1].isalpha()
                    and current[-1].islower()
                    and _CONTINUATION_RE.match(lines[i + 1])
                    and len(current) < 60
                ):
                    current = current + " " + lines[i + 1].lstrip()
                    continuation_count += 1
                    merged.append(current)
                    i += 2
                    continue
                merged.append(current)
                i += 1
            if continuation_count:
                stats["continuation_lines_merged"] = continuation_count
            modified = "\n".join(merged)

        if modified != result.text:
            result.was_modified = True
            result.stats = stats

        result.text = modified
        return result
