import re

from .base import StructureDetectionStrategy
from ...models import (
    CleanedDocument,
    DocumentStructure,
    TableOfContents,
    TableOfContentsEntry,
)


class TOCDetectionStrategy(StructureDetectionStrategy):
    operation = "detect_toc"

    # Pattern: "1. Title ........ 5" or "1. Title 5"
    _TOC_ENTRY_PATTERN = re.compile(
        r"^\s*"
        r"(\d+(?:\.\d+)*)"         # Number: 1, 1.1, etc.
        r"(?:\.)?\s+"               # Optional dot + space
        r"([A-Za-z][A-Za-z\s\-,'\(\)]{2,80}?)"  # Title text
        r"(?:\s*[\.\-\s]{2,}\s*|\s{5,})"        # Separator (dots/dashes or wide space)
        r"(\d+)\s*$",               # Page number
        re.MULTILINE,
    )

    # Simpler fallback: "1. Title   5" with at least 2 spaces between title and page
    _TOC_SIMPLE_PATTERN = re.compile(
        r"^\s*"
        r"(\d+(?:\.\d+)*)"
        r"(?:\.)?\s+"
        r"([A-Za-z][A-Za-z\s\-,'\(\)]{2,80}?)"
        r"\s{2,}"                    # At least 2 spaces between title and page
        r"(\d+)\s*$",
        re.MULTILINE,
    )

    # Last resort: "1. Title 1" with exactly one space before page number
    # Only matches when title ends with a letter and page number starts a new token
    _TOC_TIGHT_PATTERN = re.compile(
        r"^\s*"
        r"(\d+(?:\.\d+)*)"
        r"(?:\.)?\s+"
        r"([A-Za-z][A-Za-z\s\-,'\(\)]{2,80}?)"
        r"\s+"
        r"(\d+)\s*$",
        re.MULTILINE,
    )

    def __init__(self, max_lines_to_scan: int = 50, min_entries: int = 3):
        self._max_lines_to_scan = max_lines_to_scan
        self._min_entries = min_entries

    def process(self, document: CleanedDocument, structure: DocumentStructure | None = None) -> DocumentStructure:
        text = document.text.strip()
        if not text:
            result = structure or DocumentStructure(detection_strategy="toc_detection")
            return result

        scan_text = "\n".join(text.split("\n")[:self._max_lines_to_scan])

        entries: list[TableOfContentsEntry] = []
        seen_titles: set[str] = set()

        for pattern in [self._TOC_ENTRY_PATTERN, self._TOC_SIMPLE_PATTERN, self._TOC_TIGHT_PATTERN]:
            for m in pattern.finditer(scan_text):
                number = m.group(1)
                title = m.group(2).strip()
                page = int(m.group(3))

                title_lower = title.lower()
                if title_lower in seen_titles:
                    continue
                seen_titles.add(title_lower)

                level = len(number.split("."))
                entry = TableOfContentsEntry(
                    title=title,
                    level=level,
                    page_number=page,
                )
                entries.append(entry)

            if len(entries) >= self._min_entries:
                break

        result = structure or DocumentStructure(detection_strategy="toc_detection")

        if len(entries) >= self._min_entries:
            result.toc = TableOfContents(entries=entries)

        return result
