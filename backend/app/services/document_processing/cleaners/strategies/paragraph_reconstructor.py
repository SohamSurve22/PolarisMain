import re

from ...models import CleaningOperation, PageInfo
from .base import CleaningStrategy, CleansedResult


_LIST_MARKERS_RE = re.compile(r"^\s*(?:\d+[\.\)]|[a-zA-Z][\.\)]|[-*•‣⁃]|\(\d+\)|\(\w+\))\s")
_NUMBERED_HEADING_RE = re.compile(
    r"^\s*(?:\d+[\.\)]\s|\d+\.\d+\s)", re.IGNORECASE
)
_NAMED_SECTION_RE = re.compile(
    r"^\s*(?:Section|Article|Clause|Chapter|Schedule|Annexure)\s+\d+[\s\.]?",
    re.IGNORECASE,
)
_ALLCAPS_HEADING_RE = re.compile(r"^\s*[A-Z][A-Z\s]{2,40}$")


class ParagraphReconstructor(CleaningStrategy):
    def __init__(self, preserve_list_indentation: bool = True):
        self._preserve_lists = preserve_list_indentation

    @property
    def operation(self) -> CleaningOperation:
        return CleaningOperation.RECONSTRUCT_PARAGRAPHS

    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        result = CleansedResult(text=text)
        lines = text.split("\n")
        paragraphs: list[str] = []
        buffer: list[str] = []
        buffer_is_list = False
        merged_count = 0

        def flush_buffer() -> None:
            nonlocal buffer, buffer_is_list, merged_count
            if not buffer:
                return
            if buffer_is_list:
                paragraphs.extend(buffer)
            else:
                joined = " ".join(buffer)
                paragraphs.append(joined)
                if len(buffer) > 1:
                    merged_count += 1
            buffer = []
            buffer_is_list = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                flush_buffer()
                paragraphs.append("")
                continue

            is_list_item = bool(_LIST_MARKERS_RE.match(line))
            is_heading = bool(
                _NUMBERED_HEADING_RE.match(stripped)
                or _NAMED_SECTION_RE.match(stripped)
                or _ALLCAPS_HEADING_RE.match(stripped)
            )

            if is_heading:
                flush_buffer()
                paragraphs.append(stripped)
                continue

            if is_list_item:
                flush_buffer()
                paragraphs.append(stripped)
                continue

            if not buffer:
                buffer.append(stripped)
            else:
                buffer.append(stripped)

        flush_buffer()

        if lines != paragraphs:
            result.was_modified = True
            result.stats["lines_merged"] = merged_count

        result.text = "\n".join(paragraphs)
        return result
