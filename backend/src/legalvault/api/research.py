from functools import lru_cache

from fastapi import APIRouter, Depends

from legalvault.auth import AuthenticatedUser, get_current_user
from legalvault.corpus.repository import DEFAULT_CORPUS, SectionCorpus
from legalvault.graph.research import DISCLAIMER, run_research_graph
from legalvault.models.research import ResearchRequest, ResearchResponse

router = APIRouter(tags=["research"])


@lru_cache
def get_corpus() -> SectionCorpus:
    return DEFAULT_CORPUS


@router.post("/research", response_model=ResearchResponse)
def post_research(
    body: ResearchRequest,
    _user: AuthenticatedUser = Depends(get_current_user),
    corpus: SectionCorpus = Depends(get_corpus),
) -> ResearchResponse:
    state = run_research_graph(body.query, corpus=corpus)
    return ResearchResponse(
        query_mode=state["query_mode"],
        lead=state["lead"],
        body=state["body"],
        citations=state["citations"],
        confidence=state["confidence"],
        disclaimer=DISCLAIMER,
    )
