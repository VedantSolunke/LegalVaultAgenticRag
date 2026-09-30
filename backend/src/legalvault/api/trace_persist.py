from uuid import UUID

from legalvault.config import Settings
from legalvault.graph.research import GraphState, build_request_trace
from legalvault.traces.repository import TraceStore


def persist_request_trace(
    settings: Settings,
    user_id: str,
    state: GraphState,
    *,
    session_id: UUID | None = None,
) -> str | None:
    if settings.database_url is None:
        return None
    store = TraceStore.connect(settings.database_url)
    trace_id = store.insert_trace(
        user_id,
        build_request_trace(state),
        session_id=session_id,
    )
    return str(trace_id)
