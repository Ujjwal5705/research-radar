from sqlalchemy import or_, select, func
from sqlalchemy.orm import Session, selectinload

from app.models import Paper, PaperAuthor, PaperTopic, Author, Topic
from app.schemas import PaperSummaryOut, PaperDetailOut, AuthorOut, TopicOut


def to_summary(paper: Paper) -> PaperSummaryOut:
    return PaperSummaryOut(
        id=paper.id,
        title=paper.title,
        publication_year=paper.publication_year,
        citation_count=paper.citation_count,
        authors=[link.author.name for link in paper.author_links],
        topics=[link.topic.name for link in paper.topic_links],
    )


def to_detail(paper: Paper) -> PaperDetailOut:
    return PaperDetailOut(
        id=paper.id,
        openalex_id=paper.openalex_id,
        title=paper.title,
        abstract=paper.abstract,
        publication_year=paper.publication_year,
        doi=paper.doi,
        citation_count=paper.citation_count,
        authors=[
            AuthorOut(id=link.author.id, name=link.author.name)
            for link in paper.author_links
        ],
        topics=[
            TopicOut(name=link.topic.name, score=link.score)
            for link in paper.topic_links
        ],
    )


def list_papers(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    year: int | None = None,
    topic: str | None = None,
    author: str | None = None,
) -> tuple[list[Paper], int]:
    """Returns (papers_for_this_page, total_matching_count)."""

    query = select(Paper).options(
        selectinload(Paper.author_links).selectinload(PaperAuthor.author),
        selectinload(Paper.topic_links).selectinload(PaperTopic.topic),
    )

    if q:
        like = f"%{q}%"
        query = query.where(or_(Paper.title.ilike(like), Paper.abstract.ilike(like)))

    if year is not None:
        query = query.where(Paper.publication_year == year)

    if topic:
        query = (
            query.join(Paper.topic_links)
            .join(PaperTopic.topic)
            .where(Topic.name.ilike(topic))
        )

    if author:
        query = (
            query.join(Paper.author_links)
            .join(PaperAuthor.author)
            .where(Author.name.ilike(f"%{author}%"))
        )

    # Count total matches before pagination (distinct because the topic/author
    # joins above can otherwise multiply rows for papers with several matches)
    count_query = select(func.count()).select_from(
        query.with_only_columns(Paper.id).distinct().subquery()
    )
    total = db.scalar(count_query) or 0

    query = query.distinct().order_by(
        Paper.publication_year.desc().nulls_last(), Paper.id.desc()
    )
    query = query.offset((page - 1) * page_size).limit(page_size)

    papers = list(db.scalars(query).unique())
    return papers, total


def get_paper(db: Session, paper_id: int) -> Paper | None:
    query = (
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.author_links).selectinload(PaperAuthor.author),
            selectinload(Paper.topic_links).selectinload(PaperTopic.topic),
        )
    )
    return db.scalars(query).first()
