import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ListItemMatch:
    text: str
    marker: str
    marker_type: str
    level: int
    start: int
    end: int


_ALPHA_LOWER = re.compile(r"^\(([a-z])\)\s+")
_ALPHA_UPPER = re.compile(r"^\(([A-Z])\)\s+")
_ROMAN_LOWER = re.compile(
    r"^\(([ivxlcdm]+)\)\s+"
)
_ROMAN_UPPER = re.compile(
    r"^\(([IVXLCDM]+)\)\s+"
)
_DECIMAL_PAREN = re.compile(r"^\((\d+)\)\s+")
_DECIMAL_DOT = re.compile(r"^(\d+)\.\s+")
_BULLET = re.compile(r"^([\-*•⁃◦▪▸▹►→‣⁌⁍])[ \t]+")
_ROMAN_NUMERAL = re.compile(
    r"^(M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))\.\s+",
    re.IGNORECASE,
)


def detect_items(text: str) -> list[ListItemMatch]:
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    matches: list[ListItemMatch] = []
    char_offset = 0

    for line in lines:
        stripped = line.strip()
        line_len = len(line)
        if not stripped:
            char_offset += line_len + 1
            continue

        match = _match_list_item(stripped)
        if match:
            matches.append(ListItemMatch(
                text=match["text"],
                marker=match["marker"],
                marker_type=match["type"],
                level=match["level"],
                start=char_offset,
                end=char_offset + len(stripped),
            ))

        char_offset += line_len + 1

    return matches


def _match_list_item(line: str) -> dict | None:
    m = _BULLET.match(line)
    if m:
        marker = m.group(1)
        rest = line[m.end() :].strip()
        return {"text": rest, "marker": marker, "type": "bullet", "level": 1}

    m = _DECIMAL_DOT.match(line)
    if m:
        num = m.group(1)
        rest = line[m.end() :].strip()
        return {"text": rest, "marker": num + ".", "type": "decimal_dot", "level": 1}

    m = _DECIMAL_PAREN.match(line)
    if m:
        num = m.group(1)
        rest = line[m.end() :].strip()
        return {"text": rest, "marker": f"({num})", "type": "decimal_paren", "level": 3}

    m = _ROMAN_LOWER.match(line)
    if m:
        roman = m.group(1)
        rest = line[m.end() :].strip()
        return {"text": rest, "marker": f"({roman})", "type": "roman_lower", "level": 3}

    m = _ROMAN_UPPER.match(line)
    if m:
        roman = m.group(1)
        rest = line[m.end() :].strip()
        return {"text": rest, "marker": f"({roman})", "type": "roman_upper", "level": 3}

    m = _ALPHA_LOWER.match(line)
    if m:
        letter = m.group(1)
        rest = line[m.end() :].strip()
        return {"text": rest, "marker": f"({letter})", "type": "alpha_lower", "level": 2}

    m = _ALPHA_UPPER.match(line)
    if m:
        letter = m.group(1)
        rest = line[m.end() :].strip()
        return {"text": rest, "marker": f"({letter})", "type": "alpha_upper", "level": 2}

    return None


def classify_item_level(marker_type: str) -> int:
    lookup = {
        "bullet": 1,
        "decimal_dot": 1,
        "decimal_paren": 3,
        "alpha_lower": 2,
        "alpha_upper": 2,
        "roman_lower": 3,
        "roman_upper": 3,
    }
    return lookup.get(marker_type, 1)
