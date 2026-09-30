from functools import lru_cache

from fastapi import APIRouter, Depends

from legalvault.auth import AuthenticatedUser, get_current_user
from legalvault.config import get_settings
from legalvault.corpus.postgres import PostgresSectionCorpus
from legalvault.corpus.repository import DEFAULT_CORPUS, SectionCorpus
from legalvault.graph.research import DISCLAIMER, run_research_graph
from legalvault.models.research import ResearchRequest, ResearchResponse

router = APIRouter(tags=["research"])


@lru_cache
def get_corpus() -> SectionCorpus:
    settings = get_settings()
    if settings.corpus_backend == "postgres":
        if settings.database_url is None:
            raise RuntimeError(
                "LEGALVAULT_CORPUS_BACKEND=postgres requires LEGALVAULT_DATABASE_URL"
            )
        return PostgresSectionCorpus.connect(settings.database_url)
    return DEFAULT_CORPUS


def _corpus_dependency() -> SectionCorpus:
    return get_corpus()


@router.post("/research", response_model=ResearchResponse)
def post_research(
    body: ResearchRequest,
    _user: AuthenticatedUser = Depends(get_current_user),
    corpus: SectionCorpus = Depends(_corpus_dependency),
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
