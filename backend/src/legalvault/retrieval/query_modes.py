"""Heuristic query-mode classification for the research graph."""

import re

from legalvault.retrieval.ipc_lookup import is_ipc_mapping_query
from legalvault.retrieval.section_lookup import extract_section_numbers

_OUT_OF_CORPUS_PATTERNS = (
    re.compile(r"\bbnss\b", re.I),
    re.compile(r"\bbsa\b", re.I),
    re.compile(r"bharatiya\s+nagarik\s+suraksha", re.I),
    re.compile(r"bharatiya\s+sakshya", re.I),
    re.compile(r"\bcrpc\b", re.I),
    re.compile(r"criminal\s+procedure", re.I),
    re.compile(r"\bcase\s+law\b", re.I),
    re.compile(r"\bprecedent\b", re.I),
    re.compile(r"supreme\s+court\s+judgment", re.I),
)

_COMPARISON_WORDS = (
    "compare",
    "comparison",
    "difference",
    " versus ",
    " vs ",
    "differ",
)

_NARRATIVE_MARKERS = (
    " i ",
    " my ",
    " me ",
    " someone ",
    " person ",
    " attacked ",
    " threatened ",
    " assaulted ",
    " stole ",
    " damaged ",
)

_APPLICABILITY_MARKERS = (
    "which section",
    "what section",
    "could apply",
    "may apply",
    "potentially relevant",
    "sections apply",
    "provision",
)

_PURE_META_WHAT_IS_THE_BNS = re.compile(r"what is the bns\s*\??\s*$", re.I)

_GENERAL_BNS_PATTERNS = (
    "what is bharatiya nyaya",
    "when did bns",
    "how to read a bns section",
    "what does the bns cover",
)


def is_out_of_corpus_query(text: str) -> bool:
    return any(pattern.search(text) for pattern in _OUT_OF_CORPUS_PATTERNS)


def is_section_comparison_query(text: str) -> bool:
    lowered = f" {text.lower()} "
    if not any(word in lowered for word in _COMPARISON_WORDS):
        return False
    return bool(extract_section_numbers(text)) or "section" in lowered


def is_fact_pattern_query(text: str) -> bool:
    lowered = f" {text.lower()} "
    if is_section_comparison_query(text):
        return False
    has_narrative = any(marker in lowered for marker in _NARRATIVE_MARKERS)
    has_applicability = any(marker in text.lower() for marker in _APPLICABILITY_MARKERS)
    if has_narrative and has_applicability:
        return True
    if has_narrative and len(text.split()) >= 14:
        return True
    return False


def is_general_bns_information_query(text: str) -> bool:
    if extract_section_numbers(text):
        return False
    lowered = text.lower().strip()
    if _PURE_META_WHAT_IS_THE_BNS.fullmatch(lowered):
        return True
    return any(pattern in lowered for pattern in _GENERAL_BNS_PATTERNS)


def classify_query_mode(text: str) -> str:
    if is_out_of_corpus_query(text):
        return "out_of_corpus"
    if is_ipc_mapping_query(text):
        return "ipc_to_bns_mapping"
    if is_general_bns_information_query(text):
        return "general_bns_information"
    if extract_section_numbers(text) and not is_section_comparison_query(text):
        return "section_lookup"
    if is_section_comparison_query(text):
        return "section_comparison"
    if is_fact_pattern_query(text):
        return "fact_pattern_analysis"
    return "legal_concept_lookup"


def facts_are_thin(text: str) -> bool:
    if extract_section_numbers(text):
        return False
    return len(text.split()) < 12
