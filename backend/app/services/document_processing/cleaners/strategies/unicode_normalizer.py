import re
import unicodedata

from ...models import CleaningOperation, PageInfo
from .base import CleaningStrategy, CleansedResult


LIGATURE_MAP = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "st",
    "\ufb06": "st",
    "\ufb20": "ft",
    "\u00df": "ss",
}

LIGATURE_RE = re.compile("|".join(re.escape(c) for c in LIGATURE_MAP))


class UnicodeNormalizer(CleaningStrategy):
    @property
    def operation(self) -> CleaningOperation:
        return CleaningOperation.NORMALIZE_UNICODE

    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        result = CleansedResult(text=text)
        count = 0

        normalized = unicodedata.normalize("NFC", text)

        def fix_ligature(m: re.Match) -> str:
            nonlocal count
            count += 1
            return LIGATURE_MAP[m.group(0)]

        normalized = LIGATURE_RE.sub(fix_ligature, normalized)
        normalized = normalized.replace("\u2013", "\u2014")
        normalized = normalized.replace("\u2026", "...")

        if normalized != text:
            result.was_modified = True
            result.stats["ligatures_fixed"] = count
            result.stats["nfc_normalized"] = 1

        result.text = normalized
        return result
