from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from legalvault.models.research import ResearchResponse


class ChatSession(BaseModel):
    id: UUID
    user_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class SessionMessage(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    body: str
    created_at: datetime


class CreateSessionResponse(BaseModel):
    session: ChatSession


class SessionListResponse(BaseModel):
    sessions: list[ChatSession]


class PostMessageRequest(BaseModel):
    query: str = Field(min_length=1)


class PostMessageResponse(BaseModel):
    message: SessionMessage
    research: ResearchResponse
