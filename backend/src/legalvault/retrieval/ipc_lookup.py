import re

IPC_SECTION_PATTERN = re.compile(
    r"\bipc\b\s*(?:section|sec\.?|s\.?)?\s*(\d+)",
    re.IGNORECASE,
)


def extract_ipc_section_numbers(query: str) -> list[int]:
    numbers: list[int] = []
    for match in IPC_SECTION_PATTERN.finditer(query):
        numbers.append(int(match.group(1)))
    seen: set[int] = set()
    ordered: list[int] = []
    for n in numbers:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def is_ipc_mapping_query(query: str) -> bool:
    if not extract_ipc_section_numbers(query):
        return False
    lowered = query.lower()
    return "ipc" in lowered
