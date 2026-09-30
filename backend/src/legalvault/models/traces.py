from typing import Any

from pydantic import BaseModel


class RequestTraceResponse(BaseModel):
    query_mode: str
    retrieval_query: str
    retrieval_snapshot: list[dict[str, Any]]
    verification_outcome: str
    latency_ms: float
    confidence: str
