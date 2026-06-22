import re

from ...models import CleaningOperation, PageInfo
from .base import CleaningStrategy, CleansedResult


_QUOTE_MAP = str.maketrans({
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u201f": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u201b": "'",
    "\u2039": "'",
    "\u203a": "'",
    "\u00ab": '"',
    "\u00bb": '"',
})

_CONSECUTIVE_QUOTES_RE = re.compile(r'""')
_LONG_DASH_RE = re.compile(r"[—–−]")
_ELLIPSIS_RE = re.compile(r"\.\.\.")


class QuotationNormalizer(CleaningStrategy):
    @property
    def operation(self) -> CleaningOperation:
        return CleaningOperation.NORMALIZE_QUOTES

    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        result = CleansedResult(text=text)
        count = 0

        modified = text.translate(_QUOTE_MAP)

        def count_quotes(m: re.Match) -> str:
            nonlocal count
            count += 1
            return '"'

        modified = _CONSECUTIVE_QUOTES_RE.sub(count_quotes, modified)
        modified = _LONG_DASH_RE.sub("\u2014", modified)
        modified = _ELLIPSIS_RE.sub("...", modified)

        if modified != text:
            result.was_modified = True
            result.stats["quotes_normalized"] = count

        result.text = modified
        return result
