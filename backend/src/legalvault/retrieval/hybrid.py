"""Hybrid retrieval helpers: fuse ranked section lists (section id, keyword, semantic)."""

from __future__ import annotations

from legalvault.models.research import SectionRecord

RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: list[list[SectionRecord]],
    *,
    limit: int = 5,
) -> list[SectionRecord]:
    scores: dict[int, float] = {}
    records: dict[int, SectionRecord] = {}
    for ranked in ranked_lists:
        for rank, section in enumerate(ranked, start=1):
            scores[section.section_number] = scores.get(section.section_number, 0.0) + (
                1.0 / (RRF_K + rank)
            )
            records[section.section_number] = section
    ordered_numbers = sorted(scores.keys(), key=lambda n: scores[n], reverse=True)
    return [records[n] for n in ordered_numbers[:limit]]
