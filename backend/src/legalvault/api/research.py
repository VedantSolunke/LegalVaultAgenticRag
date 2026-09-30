from functools import lru_cache
from typing import cast

from fastapi import APIRouter, Depends

from legalvault.auth import AuthenticatedUser, get_current_user
from legalvault.config import get_settings
from legalvault.corpus.mapping_repository import DEFAULT_MAPPING_STORE
from legalvault.corpus.postgres import PostgresSectionCorpus
from legalvault.corpus.postgres_mapping import PostgresMappingStore
from legalvault.corpus.repository import DEFAULT_CORPUS, SectionCorpus
from legalvault.graph.research import DISCLAIMER, MappingLookup, run_research_graph
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


@lru_cache
def get_mapping_store() -> MappingLookup:
    settings = get_settings()
    if settings.corpus_backend == "postgres":
        if settings.database_url is None:
            raise RuntimeError(
                "LEGALVAULT_CORPUS_BACKEND=postgres requires LEGALVAULT_DATABASE_URL"
            )
        return cast(MappingLookup, PostgresMappingStore.connect(settings.database_url))
    return DEFAULT_MAPPING_STORE


def _corpus_dependency() -> SectionCorpus:
    return get_corpus()


def _mapping_dependency() -> MappingLookup:
    return get_mapping_store()


@router.post("/research", response_model=ResearchResponse)
def post_research(
    body: ResearchRequest,
    _user: AuthenticatedUser = Depends(get_current_user),
    corpus: SectionCorpus = Depends(_corpus_dependency),
    mapping_store: MappingLookup = Depends(_mapping_dependency),
) -> ResearchResponse:
    state = run_research_graph(
        body.query,
        corpus=corpus,
        mapping_store=mapping_store,
    )
    return ResearchResponse(
        query_mode=state["query_mode"],
        lead=state["lead"],
        body=state["body"],
        citations=state["citations"],
        confidence=state["confidence"],
        disclaimer=DISCLAIMER,
    )
