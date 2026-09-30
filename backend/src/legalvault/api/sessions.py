from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from legalvault.api.research import _corpus_dependency, _mapping_dependency
from legalvault.auth import AuthenticatedUser, get_current_user
from legalvault.api.trace_persist import persist_request_trace
from legalvault.config import Settings, get_settings
from legalvault.corpus.repository import SectionCorpus
from legalvault.graph.research import DISCLAIMER, MappingLookup, run_research_graph
from legalvault.models.research import ResearchResponse
from legalvault.models.sessions import (
    CreateSessionResponse,
    PostMessageRequest,
    PostMessageResponse,
    SessionListResponse,
)
from legalvault.sessions.repository import SessionStore

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _require_session_store(
    settings: Settings = Depends(get_settings),
) -> SessionStore:
    if settings.database_url is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat sessions require LEGALVAULT_DATABASE_URL",
        )
    return SessionStore.connect(settings.database_url)


def _research_response_from_state(state: dict) -> ResearchResponse:
    return ResearchResponse(
        query_mode=state["query_mode"],
        lead=state["lead"],
        body=state["body"],
        citations=state["citations"],
        confidence=state["confidence"],
        disclaimer=DISCLAIMER,
    )


def _assistant_live_body(research: ResearchResponse) -> str:
    return f"{research.lead}\n\n{research.body}"


@router.post("", response_model=CreateSessionResponse)
def create_session(
    user: AuthenticatedUser = Depends(get_current_user),
    store: SessionStore = Depends(_require_session_store),
) -> CreateSessionResponse:
    session = store.create_session(user.user_id)
    return CreateSessionResponse(session=session)


@router.get("", response_model=SessionListResponse)
def list_sessions(
    user: AuthenticatedUser = Depends(get_current_user),
    store: SessionStore = Depends(_require_session_store),
) -> SessionListResponse:
    sessions = store.list_sessions(user.user_id)
    return SessionListResponse(sessions=sessions)


@router.post("/{session_id}/messages", response_model=PostMessageResponse)
def post_session_message(
    session_id: UUID,
    body: PostMessageRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    store: SessionStore = Depends(_require_session_store),
    corpus: SectionCorpus = Depends(_corpus_dependency),
    mapping_store: MappingLookup = Depends(_mapping_dependency),
    settings: Settings = Depends(get_settings),
) -> PostMessageResponse:
    session = store.get_session_for_user(user.user_id, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    history = store.get_message_bodies(session_id)
    state = run_research_graph(
        body.query,
        corpus=corpus,
        mapping_store=mapping_store,
        conversation_history=history,
    )
    research = _research_response_from_state(state)
    trace_id = persist_request_trace(
        settings,
        user.user_id,
        state,
        session_id=session_id,
    )
    if trace_id is not None:
        research = research.model_copy(update={"trace_id": trace_id})

    user_message = store.append_message(
        session_id,
        role="user",
        live_body=body.query,
    )
    store.append_message(
        session_id,
        role="assistant",
        live_body=_assistant_live_body(research),
        research=research,
    )

    return PostMessageResponse(message=user_message, research=research)
