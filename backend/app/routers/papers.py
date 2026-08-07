import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import PaginatedPapers, PaperDetailOut

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
