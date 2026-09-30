import time
from typing import Any, Protocol, TypedDict

from legalvault.corpus.mapping_repository import DEFAULT_MAPPING_STORE
from legalvault.corpus.repository import DEFAULT_CORPUS, SectionCorpus
from legalvault.models.mapping import MappingRecord
from legalvault.models.research import SectionCitation, SectionRecord
from legalvault.providers.stubs import StubLLMProvider
from legalvault.retrieval.ipc_lookup import extract_ipc_section_numbers
from legalvault.retrieval.query_modes import classify_query_mode, facts_are_thin
from legalvault.retrieval.section_lookup import extract_section_numbers
from legalvault.sessions.context import build_retrieval_query
from legalvault.verification.evidence import (
    citations_supported,
    prose_references_only_retrieved_sections,
)

DISCLAIMER = (
    "LegalVault is a legal research assistant, not legal advice. "
    "Verify all citations against the underlying statute."
)


class MappingLookup(Protocol):
    def lookup_by_ipc_numbers(self, numbers: list[int]) -> list[MappingRecord]: ...

    @property
    def known_ipc_sections(self) -> frozenset[int]: ...


class GraphState(TypedDict):
    query: str
    retrieval_query: str
    query_mode: str
    requested_section_numbers: list[int]
    requested_ipc_section_numbers: list[int]
    retrieved_mappings: list[MappingRecord]
    retrieved_sections: list[SectionRecord]
    lead: str
    body: str
    citations: list[SectionCitation]
    confidence: str
    verification_outcome: str
    latency_ms: float


def _excerpt(text: str, max_len: int = 280) -> str:
    trimmed = text.strip()
    if len(trimmed) <= max_len:
        return trimmed
    return trimmed[: max_len - 1].rstrip() + "…"


def classify_query(state: GraphState) -> GraphState:
    classification_text = state["retrieval_query"]
    mode = classify_query_mode(classification_text)
    if mode == "ipc_to_bns_mapping":
        return {
            **state,
            "query_mode": mode,
            "requested_ipc_section_numbers": extract_ipc_section_numbers(
                classification_text
            ),
            "requested_section_numbers": [],
        }
    numbers = extract_section_numbers(classification_text)
    return {
        **state,
        "query_mode": mode,
        "requested_section_numbers": numbers,
        "requested_ipc_section_numbers": [],
    }


def retrieve_mappings(
    state: GraphState, *, mapping_store: MappingLookup
) -> GraphState:
    if state["query_mode"] != "ipc_to_bns_mapping":
        return {**state, "retrieved_mappings": []}
    mappings = mapping_store.lookup_by_ipc_numbers(
        state["requested_ipc_section_numbers"]
    )
    return {**state, "retrieved_mappings": mappings}


def retrieve_sections(state: GraphState, *, corpus: SectionCorpus) -> GraphState:
    if state["query_mode"] in ("out_of_corpus", "general_bns_information"):
        return {**state, "retrieved_sections": []}

    if state["query_mode"] == "ipc_to_bns_mapping":
        bns_numbers: list[int] = []
        for mapping in state["retrieved_mappings"]:
            for number in mapping.bns_section_numbers:
                if number not in bns_numbers:
                    bns_numbers.append(number)
        sections = corpus.lookup_by_section_numbers(bns_numbers)
        return {**state, "retrieved_sections": sections}

    sections = corpus.hybrid_retrieve(
        state["retrieval_query"],
        section_numbers=state["requested_section_numbers"],
    )
    return {**state, "retrieved_sections": sections}


def _mapping_provenance_citation(
    mapping: MappingRecord,
) -> SectionCitation:
    targets = ", ".join(str(n) for n in mapping.bns_section_numbers)
    ipc_title = mapping.ipc_title or "IPC section"
    return SectionCitation(
        section_number=mapping.ipc_section_number,
        title=f"{ipc_title} (IPC → BNS mapping)",
        excerpt=(
            f"Ingested mapping links IPC section {mapping.ipc_section_number} "
            f"to BNS section(s) {targets}."
        ),
        act="IPC",
        ipc_section_number=mapping.ipc_section_number,
        mapping_source=mapping.source,
    )


def compose_response(
    state: GraphState, *, llm: StubLLMProvider
) -> GraphState:
    if state["query_mode"] == "out_of_corpus":
        draft = llm.compose_out_of_corpus(query=state["query"])
        return {
            **state,
            "lead": draft.lead,
            "body": draft.body,
            "citations": [],
            "confidence": "low",
        }

    if state["query_mode"] == "general_bns_information":
        draft = llm.compose_general_bns_information()
        return {
            **state,
            "lead": draft.lead,
            "body": draft.body,
            "citations": [],
            "confidence": "medium",
        }

    if state["query_mode"] == "ipc_to_bns_mapping":
        if not state["retrieved_mappings"]:
            return {
                **state,
                "lead": (
                    "No ingested IPC→BNS mapping records were found for this query."
                ),
                "body": (
                    "Try a known IPC section from the curated mapping datasets, "
                    "for example “What happened to IPC section 302?”"
                ),
                "citations": [],
                "confidence": "low",
            }

        mapping = state["retrieved_mappings"][0]
        citations: list[SectionCitation] = [_mapping_provenance_citation(mapping)]
        for section in state["retrieved_sections"]:
            citations.append(
                SectionCitation(
                    section_number=section.section_number,
                    title=section.title,
                    excerpt=_excerpt(section.text),
                    act=section.act,
                    ipc_section_number=mapping.ipc_section_number,
                    mapping_source=mapping.source,
                )
            )

        draft = llm.compose_ipc_mapping(
            ipc_section_number=mapping.ipc_section_number,
            ipc_title=mapping.ipc_title,
            mapping_source=mapping.source,
            bns_sections=state["retrieved_sections"],
        )
        return {
            **state,
            "lead": draft.lead,
            "body": draft.body,
            "citations": citations,
            "confidence": "high" if state["retrieved_sections"] else "low",
        }

    if not state["retrieved_sections"] and state["query_mode"] not in (
        "fact_pattern_analysis",
        "section_comparison",
    ):
        return {
            **state,
            "lead": "No matching BNS section records were found in the corpus for this query.",
            "body": (
                "Try a direct section lookup such as “BNS section 101”, "
                "or ask about a section number present in the indexed corpus."
            ),
            "citations": [],
            "confidence": "low",
        }

    citations = [
        SectionCitation(
            section_number=s.section_number,
            title=s.title,
            excerpt=_excerpt(s.text),
            act=s.act,
        )
        for s in state["retrieved_sections"]
    ]

    if state["query_mode"] == "fact_pattern_analysis":
        thin = facts_are_thin(state["query"])
        draft = llm.compose_fact_pattern(
            query=state["query"],
            sections=state["retrieved_sections"],
            thin_facts=thin,
        )
        if not state["retrieved_sections"]:
            confidence = "low"
        elif thin:
            confidence = "low"
        else:
            confidence = "high"
        return {
            **state,
            "lead": draft.lead,
            "body": draft.body,
            "citations": citations,
            "confidence": confidence,
        }

    if state["query_mode"] == "section_comparison":
        draft = llm.compose_section_comparison(sections=state["retrieved_sections"])
        return {
            **state,
            "lead": draft.lead,
            "body": draft.body,
            "citations": citations,
            "confidence": "high" if len(state["retrieved_sections"]) >= 2 else "medium",
        }

    if state["query_mode"] == "legal_concept_lookup":
        draft = llm.compose_legal_concept_lookup(
            query=state["query"],
            sections=state["retrieved_sections"],
        )
        body = draft.body
    else:
        primary = state["retrieved_sections"][0]
        primary_excerpt = _excerpt(primary.text)
        draft = llm.compose_section_lookup(
            section_number=primary.section_number,
            title=primary.title,
            excerpt=primary_excerpt,
        )

        if len(state["retrieved_sections"]) > 1:
            extra = ", ".join(
                str(s.section_number) for s in state["retrieved_sections"][1:]
            )
            body = draft.body + f"\n\nAlso retrieved from the corpus: sections {extra}."
        else:
            body = draft.body

    return {
        **state,
        "lead": draft.lead,
        "body": body,
        "citations": citations,
        "confidence": "high",
    }


def verify_citations(
    state: GraphState,
    *,
    corpus: SectionCorpus,
    mapping_store: MappingLookup,
) -> GraphState:
    if state["query_mode"] == "ipc_to_bns_mapping":
        verified: list[SectionCitation] = []
        for citation in state["citations"]:
            if citation.act == "IPC":
                mapping = mapping_store.lookup_by_ipc_numbers(
                    [citation.section_number]
                )
                if mapping:
                    verified.append(citation)
                continue
            if citation.section_number in corpus.known_section_numbers:
                if citation.ipc_section_number is None:
                    verified.append(citation)
                    continue
                mapping = mapping_store.lookup_by_ipc_numbers(
                    [citation.ipc_section_number]
                )
                if (
                    mapping
                    and citation.section_number in mapping[0].bns_section_numbers
                ):
                    verified.append(citation)
        return {**state, "citations": verified}

    allowed = corpus.known_section_numbers
    verified = [c for c in state["citations"] if c.section_number in allowed]
    return {**state, "citations": verified}


_REFUSAL_LEAD = (
    "The draft answer could not be verified against retrieved evidence."
)
_REFUSAL_BODY = (
    "Try a direct BNS section lookup or add more specific facts so retrieval "
    "can support any statutory claims."
)


def verify_evidence(
    state: GraphState,
    *,
    corpus: SectionCorpus,
    mapping_store: MappingLookup,
    llm: StubLLMProvider,
) -> GraphState:
    state = verify_citations(state, corpus=corpus, mapping_store=mapping_store)
    mode = state["query_mode"]

    if mode == "out_of_corpus":
        return {**state, "verification_outcome": "skipped_out_of_corpus"}

    if mode == "general_bns_information":
        return {**state, "verification_outcome": "skipped_meta"}

    if mode in ("fact_pattern_analysis", "section_comparison"):
        allowed = frozenset(s.section_number for s in state["retrieved_sections"])
        combined = f"{state['lead']}\n{state['body']}"
        citations_ok = citations_supported(
            state["citations"],
            allowed_section_numbers=allowed,
        )
        prose_ok = prose_references_only_retrieved_sections(
            combined,
            allowed_section_numbers=allowed,
        )
        faith_ok = llm.check_faithfulness(
            lead=state["lead"],
            body=state["body"],
            allowed_section_numbers=allowed,
        )
        if not state["retrieved_sections"]:
            return {**state, "verification_outcome": "passed_no_retrieval"}
        if citations_ok and prose_ok and faith_ok:
            return {**state, "verification_outcome": "passed"}
        return {
            **state,
            "lead": _REFUSAL_LEAD,
            "body": _REFUSAL_BODY,
            "confidence": "low",
            "verification_outcome": "failed_faithfulness",
        }

    return {**state, "verification_outcome": "passed_citations"}


def build_request_trace(state: GraphState) -> dict[str, Any]:
    snapshot = [
        {
            "section_number": section.section_number,
            "title": section.title,
            "act": section.act,
        }
        for section in state["retrieved_sections"]
    ]
    return {
        "query_mode": state["query_mode"],
        "retrieval_query": state["retrieval_query"],
        "retrieval_snapshot": snapshot,
        "verification_outcome": state["verification_outcome"],
        "latency_ms": state["latency_ms"],
        "confidence": state["confidence"],
    }


def _compile_graph(
    corpus: SectionCorpus,
    mapping_store: MappingLookup,
    llm: StubLLMProvider,
):
    from langgraph.graph import END, StateGraph

    graph = StateGraph(GraphState)
    graph.add_node("classify", classify_query)
    graph.add_node(
        "retrieve_mappings",
        lambda state: retrieve_mappings(state, mapping_store=mapping_store),
    )
    graph.add_node(
        "retrieve",
        lambda state: retrieve_sections(state, corpus=corpus),
    )
    graph.add_node(
        "compose",
        lambda state: compose_response(state, llm=llm),
    )
    graph.add_node(
        "verify",
        lambda state: verify_evidence(
            state, corpus=corpus, mapping_store=mapping_store, llm=llm
        ),
    )

    graph.set_entry_point("classify")
    graph.add_edge("classify", "retrieve_mappings")
    graph.add_edge("retrieve_mappings", "retrieve")
    graph.add_edge("retrieve", "compose")
    graph.add_edge("compose", "verify")
    graph.add_edge("verify", END)
    return graph.compile()


_DEFAULT_CORPUS = DEFAULT_CORPUS
_DEFAULT_MAPPING_STORE = DEFAULT_MAPPING_STORE
_DEFAULT_LLM = StubLLMProvider()
_COMPILED_GRAPH = _compile_graph(
    _DEFAULT_CORPUS, _DEFAULT_MAPPING_STORE, _DEFAULT_LLM
)


def run_research_graph(
    query: str,
    *,
    corpus: SectionCorpus,
    mapping_store: MappingLookup | None = None,
    llm: StubLLMProvider | None = None,
    conversation_history: list[tuple[str, str]] | None = None,
) -> GraphState:
    """Minimal in-process LangGraph pipeline for BNS research."""
    llm = llm or _DEFAULT_LLM
    mapping_store = mapping_store or _DEFAULT_MAPPING_STORE
    app = (
        _COMPILED_GRAPH
        if (
            corpus is _DEFAULT_CORPUS
            and mapping_store is _DEFAULT_MAPPING_STORE
            and llm is _DEFAULT_LLM
        )
        else _compile_graph(corpus, mapping_store, llm)
    )
    retrieval_query = build_retrieval_query(query, conversation_history)
    initial: GraphState = {
        "query": query,
        "retrieval_query": retrieval_query,
        "query_mode": "",
        "requested_section_numbers": [],
        "requested_ipc_section_numbers": [],
        "retrieved_mappings": [],
        "retrieved_sections": [],
        "lead": "",
        "body": "",
        "citations": [],
        "confidence": "low",
        "verification_outcome": "pending",
        "latency_ms": 0.0,
    }
    started = time.perf_counter()
    final = app.invoke(initial)
    final["latency_ms"] = (time.perf_counter() - started) * 1000.0
    if final.get("verification_outcome") == "pending":
        final["verification_outcome"] = "passed_citations"
    return final
