import re

SECTION_NUMBER_PATTERN = re.compile(
    r"(?:\bbns\b\s*(?:section|sec\.?|s\.?)?\s*(\d+))|"
    r"(?:\bsection\s*(\d+)\b)",
    re.IGNORECASE,
)


def extract_section_numbers(query: str) -> list[int]:
    numbers: list[int] = []
    for match in SECTION_NUMBER_PATTERN.finditer(query):
        raw = match.group(1) or match.group(2)
        if raw is not None:
            numbers.append(int(raw))
    # Deduplicate while preserving order
    seen: set[int] = set()
    ordered: list[int] = []
    for n in numbers:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered
