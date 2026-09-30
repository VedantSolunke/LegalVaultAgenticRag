from typing import Protocol, TypedDict

from legalvault.corpus.mapping_repository import DEFAULT_MAPPING_STORE
from legalvault.corpus.repository import DEFAULT_CORPUS, SectionCorpus
from legalvault.models.mapping import MappingRecord
from legalvault.models.research import SectionCitation, SectionRecord
from legalvault.providers.stubs import StubLLMProvider
from legalvault.retrieval.ipc_lookup import (
    extract_ipc_section_numbers,
    is_ipc_mapping_query,
)
from legalvault.retrieval.section_lookup import extract_section_numbers
from legalvault.sessions.context import build_retrieval_query

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


def _excerpt(text: str, max_len: int = 280) -> str:
    trimmed = text.strip()
    if len(trimmed) <= max_len:
        return trimmed
    return trimmed[: max_len - 1].rstrip() + "…"


def classify_query(state: GraphState) -> GraphState:
    classification_text = state["retrieval_query"]
    if is_ipc_mapping_query(classification_text):
        return {
            **state,
            "query_mode": "ipc_to_bns_mapping",
            "requested_ipc_section_numbers": extract_ipc_section_numbers(
                classification_text
            ),
            "requested_section_numbers": [],
        }
    numbers = extract_section_numbers(classification_text)
    if numbers:
        return {
            **state,
            "query_mode": "section_lookup",
            "requested_section_numbers": numbers,
            "requested_ipc_section_numbers": [],
        }
    return {
        **state,
        "query_mode": "legal_concept_lookup",
        "requested_section_numbers": [],
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

    if not state["retrieved_sections"]:
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
        lambda state: verify_citations(
            state, corpus=corpus, mapping_store=mapping_store
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
    }
    return app.invoke(initial)
