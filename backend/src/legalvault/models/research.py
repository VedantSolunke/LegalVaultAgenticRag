from pydantic import BaseModel, Field


class SectionRecord(BaseModel):
    section_number: int
    title: str
    chapter: str
    text: str
    act: str = "BNS"


class SectionCitation(BaseModel):
    section_number: int
    title: str
    excerpt: str
    act: str = "BNS"


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1)
    session_id: str | None = None


class ResearchResponse(BaseModel):
    query_mode: str
    lead: str
    body: str
    citations: list[SectionCitation]
    confidence: str
    disclaimer: str
