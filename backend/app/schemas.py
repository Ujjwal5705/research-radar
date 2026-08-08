from pydantic import BaseModel, ConfigDict


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    score: float


class PaperSummaryOut(BaseModel):
    """Shape returned in the /papers list - deliberately lighter than the
    detail view (no full abstract) so list pages stay fast."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    publication_year: int | None
    citation_count: int
    authors: list[str]
    topics: list[str]


class PaperDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    openalex_id: str
    title: str
    abstract: str | None
    publication_year: int | None
    doi: str | None
    citation_count: int
    authors: list[AuthorOut]
    topics: list[TopicOut]


class PaginatedPapers(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    results: list[PaperSummaryOut]


class SummaryOut(BaseModel):
    summary: str
