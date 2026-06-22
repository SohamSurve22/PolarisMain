import re


_ABBREVIATIONS = frozenset({
    "mr", "mrs", "ms", "mx", "dr", "prof", "rev", "hon", "st",
    "inc", "ltd", "corp", "llc", "co", "dept", "est", "govt",
    "e.g", "i.e", "vs", "v", "al", "cf", "ff",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "ch", "art", "sec", "cl", "para", "sch", "app", "ex",
    "no", "vol", "pp", "p", "ca", "dba", "aka", "et",
    "gen", "mgr", "asst",
    "u.s", "u.k", "e.u",
    "a.m", "p.m",
})

_SENTENCE_SPLIT = re.compile(
    r"([.!?][\"']?)\s+(?=[A-Z\"'(])"
)


def split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    text = re.sub(r"\s+", " ", text).strip()

    candidates: list[str] = []
    last_end = 0
    for m in _SENTENCE_SPLIT.finditer(text):
        candidates.append(text[last_end : m.end(1)])
        last_end = m.end()
    candidates.append(text[last_end:])
    candidates = [c.strip() for c in candidates if c.strip()]

    if not candidates:
        return [text]

    result: list[str] = [candidates[0]]
    for candidate in candidates[1:]:
        prev = result[-1]
        if _should_merge(prev, candidate):
            result[-1] = prev + " " + candidate
        else:
            result.append(candidate)

    return result


def _should_merge(prev: str, curr: str) -> bool:
    prev_word = _last_word(prev)
    if not prev_word:
        return False

    prev_stripped = prev_word.rstrip(".").lower()

    if prev_stripped in _ABBREVIATIONS:
        return True

    if re.search(r"(^|\s)[A-Z]\.$", prev):
        return True

    if prev_word.endswith(".") and len(prev_word) <= 3:
        core = prev_word.rstrip(".")
        if core and core[-1].isalpha():
            return True

    return False


def _last_word(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    parts = text.split()
    return parts[-1] if parts else ""
