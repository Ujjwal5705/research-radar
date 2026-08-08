import math
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import PaginatedPapers, PaperDetailOut, SummaryOut
from app.ai.summarize import summarize_abstract

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=PaginatedPapers)
def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Keyword search on title and abstract"),
    year: int | None = Query(None, description="Filter by publication year"),
    topic: str | None = Query(None, description="Filter by topic name"),
    author: str | None = Query(
        None, description="Filter by author name (partial match)"
    ),
    db: Session = Depends(get_db),
):
    papers, total = crud.list_papers(
        db, page=page, page_size=page_size, q=q, year=year, topic=topic, author=author
    )
    total_pages = math.ceil(total / page_size) if total else 0
    return PaginatedPapers(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=[crud.to_summary(p) for p in papers],
    )


@router.get("/{paper_id}", response_model=PaperDetailOut)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = crud.get_paper(db, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return crud.to_detail(paper)


@router.post("/{paper_id}/summarize", response_model=SummaryOut)
def summarize_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = crud.get_paper(db, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.abstract or not paper.abstract.strip():
        raise HTTPException(
            status_code=422, detail="This paper has no abstract to summarize."
        )

    try:
        summary = summarize_abstract(paper.abstract)
    except RuntimeError as e:
        # Missing API key or empty model response - a config/setup problem.
        logger.error("Summarize config error for paper %s: %s", paper_id, e)
        raise HTTPException(
            status_code=503, detail="AI summarization is not configured correctly."
        )
    except Exception as e:
        # Groq API errors (rate limit, network, etc.) - transient, retryable.
        logger.error("Summarize failed for paper %s: %s", paper_id, e)
        raise HTTPException(
            status_code=502,
            detail="AI summarization service is currently unavailable. Please try again.",
        )

    return SummaryOut(summary=summary)
