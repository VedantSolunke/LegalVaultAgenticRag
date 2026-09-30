from typing import TypedDict

from legalvault.corpus.repository import DEFAULT_CORPUS, SectionCorpus
from legalvault.models.research import SectionCitation, SectionRecord
from legalvault.providers.stubs import StubLLMProvider
from legalvault.retrieval.section_lookup import extract_section_numbers

DISCLAIMER = (
    "LegalVault is a legal research assistant, not legal advice. "
    "Verify all citations against the underlying statute."
)


class GraphState(TypedDict):
    query: str
    query_mode: str
    requested_section_numbers: list[int]
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
    numbers = extract_section_numbers(state["query"])
    if numbers:
        return {
            **state,
            "query_mode": "section_lookup",
            "requested_section_numbers": numbers,
        }
    return {
        **state,
        "query_mode": "legal_concept_lookup",
        "requested_section_numbers": [],
    }


def retrieve_sections(state: GraphState, *, corpus: SectionCorpus) -> GraphState:
    sections = corpus.hybrid_retrieve(
        state["query"],
        section_numbers=state["requested_section_numbers"],
    )
    return {**state, "retrieved_sections": sections}


def compose_response(
    state: GraphState, *, llm: StubLLMProvider
) -> GraphState:
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


def verify_citations(state: GraphState, *, corpus: SectionCorpus) -> GraphState:
    allowed = corpus.known_section_numbers
    verified = [c for c in state["citations"] if c.section_number in allowed]
    return {**state, "citations": verified}


def _compile_graph(
    corpus: SectionCorpus,
    llm: StubLLMProvider,
):
    from langgraph.graph import END, StateGraph

    graph = StateGraph(GraphState)
    graph.add_node("classify", classify_query)
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
        lambda state: verify_citations(state, corpus=corpus),
    )

    graph.set_entry_point("classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "compose")
    graph.add_edge("compose", "verify")
    graph.add_edge("verify", END)
    return graph.compile()


_DEFAULT_CORPUS = DEFAULT_CORPUS
_DEFAULT_LLM = StubLLMProvider()
_COMPILED_GRAPH = _compile_graph(_DEFAULT_CORPUS, _DEFAULT_LLM)


def run_research_graph(
    query: str,
    *,
    corpus: SectionCorpus,
    llm: StubLLMProvider | None = None,
) -> GraphState:
    """Minimal in-process LangGraph pipeline for section lookup."""
    llm = llm or _DEFAULT_LLM
    app = (
        _COMPILED_GRAPH
        if corpus is _DEFAULT_CORPUS and llm is _DEFAULT_LLM
        else _compile_graph(corpus, llm)
    )
    initial: GraphState = {
        "query": query,
        "query_mode": "",
        "requested_section_numbers": [],
        "retrieved_sections": [],
        "lead": "",
        "body": "",
        "citations": [],
        "confidence": "low",
    }
    return app.invoke(initial)
