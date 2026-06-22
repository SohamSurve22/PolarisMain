import re
from dataclasses import dataclass, field
from typing import Any

from .base import StructureDetectionStrategy
from ...models import (
    CleanedDocument,
    DocumentStructure,
    StructuralElement,
    StructuralElementType,
)


@dataclass
class HeadingMatch:
    text: str
    level: int
    confidence: float
    char_start: int
    char_end: int
    line_number: int
    pattern_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class HeadingDetectionStrategy(StructureDetectionStrategy):
    operation = "detect_headings"

    _PATTERNS = [
        (r"^(\d+)\.(\d+)\.(\d+)\.?\s+(?=[A-Z(])", "decimal_3", 0.95, lambda m: 3),
        (r"^(\d+)\.(\d+)\.?\s+(?=[A-Z(])", "decimal_2", 0.95, lambda m: 2),
        (r"^(\d+)\.\s+(?=[A-Z(])", "decimal_1", 0.95, lambda m: 1),
        (r"^(Section|Article|Clause|Rule|Regulation)\s+(\d+)\.(\d+)\.(\d+)\s*[\.:]?\s+(?=[A-Z(])", "named_3", 0.9, lambda m: 3),
        (r"^(Section|Article|Clause|Rule|Regulation)\s+(\d+)\.(\d+)\s*[\.:]?\s+(?=[A-Z(])", "named_2", 0.9, lambda m: 2),
        (r"^(Section|Article|Clause|Rule|Regulation)\s+(\d+)\s*[\.:]?\s+(?=[A-Z(])", "named_1", 0.9, lambda m: 1),
        (r"^(Schedule|Appendix|Annexure|Exhibit|Attachment)\s+([A-Z\d]+)\s*[:\.]?[ \t]*", "division", 0.9, lambda m: 0),
        (r"^([IVXLCDM]+)\.\s+(?=[A-Z])", "roman", 0.8, lambda m: 1),
        (r"^([A-Z])\.\s+(?=[A-Z])", "alpha", 0.5, lambda m: 2),
        (r"^[A-Z][A-Z\s\-\(\),]{2,50}$", "allcaps", 0.6, lambda m: 1),
    ]

    def __init__(self, min_confidence: float = 0.5, custom_patterns: list[str] | None = None):
        self._min_confidence = min_confidence
        self._custom_patterns = custom_patterns or []
        self._compiled = [
            (re.compile(pat), name, conf, fn)
            for pat, name, conf, fn in self._PATTERNS
        ]

    def process(self, document: CleanedDocument, structure: DocumentStructure | None = None) -> DocumentStructure:
        text = document.text
        if not text.strip():
            return DocumentStructure(detection_strategy="heading_detection")

        lines = text.split("\n")
        matches: list[HeadingMatch] = []
        char_offset = 0

        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            line_len = len(line)
            if not stripped:
                char_offset += line_len + 1
                continue

            best_level = 0
            best_confidence = 0.0
            best_name = ""
            best_match_obj = None

            for pattern, name, confidence, level_fn in self._compiled:
                m = pattern.match(stripped)
                if m and confidence >= self._min_confidence and confidence > best_confidence:
                    best_level = level_fn(m)
                    best_confidence = confidence
                    best_name = name
                    best_match_obj = m

            for idx, custom_pat in enumerate(self._custom_patterns):
                try:
                    cp = re.compile(custom_pat)
                    m = cp.match(stripped)
                    if m:
                        confidence = 0.5
                        if confidence > best_confidence and confidence >= self._min_confidence:
                            best_level = 1
                            best_confidence = confidence
                            best_name = f"custom_{idx}"
                            best_match_obj = m
                except re.error:
                    continue

            if best_match_obj is not None:
                matches.append(HeadingMatch(
                    text=stripped,
                    level=best_level,
                    confidence=best_confidence,
                    char_start=char_offset,
                    char_end=char_offset + line_len,
                    line_number=line_idx + 1,
                    pattern_type=best_name,
                ))

            char_offset += line_len + 1

        result = DocumentStructure(detection_strategy="heading_detection")
        for i, m in enumerate(matches):
            elem_type = self._determine_type(m.level, m.text)
            element = StructuralElement(
                element_id=f"h_{i + 1}",
                type=elem_type,
                text=m.text,
                level=m.level,
                metadata={
                    "char_start": m.char_start,
                    "char_end": m.char_end,
                    "line_number": m.line_number,
                    "confidence": m.confidence,
                    "pattern_type": m.pattern_type,
                },
            )
            result.elements[element.element_id] = element

        result.root_element_ids = [
            eid for eid, e in result.elements.items() if e.level <= 1
        ]
        return result

    @staticmethod
    def _determine_type(level: int, text: str) -> StructuralElementType:
        if level == 0:
            return StructuralElementType.SCHEDULE
        if level == 1:
            return StructuralElementType.HEADING
        return StructuralElementType.SUBHEADING
