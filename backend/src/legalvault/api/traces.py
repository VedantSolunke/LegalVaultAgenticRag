from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from legalvault.auth import AuthenticatedUser, require_admin
from legalvault.config import Settings, get_settings
from legalvault.models.traces import RequestTraceResponse
from legalvault.traces.repository import TraceStore

router = APIRouter(prefix="/traces", tags=["traces"])


def _trace_store(settings: Settings = Depends(get_settings)) -> TraceStore:
    if settings.database_url is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Traces require LEGALVAULT_DATABASE_URL",
        )
    return TraceStore.connect(settings.database_url)


@router.get("/{trace_id}", response_model=RequestTraceResponse)
def get_request_trace(
    trace_id: UUID,
    _admin: AuthenticatedUser = Depends(require_admin),
    store: TraceStore = Depends(_trace_store),
) -> RequestTraceResponse:
    trace = store.get_trace(trace_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found",
        )
    return RequestTraceResponse.model_validate(trace)
