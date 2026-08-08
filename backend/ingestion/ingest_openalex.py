"""
Idempotent ingestion script: pulls recent papers from OpenAlex for a fixed
set of topics and upserts them into Postgres.

Safe to re-run: every entity (paper, author, topic) is matched on a stable
natural key before insert, so re-running never creates duplicates - it just
refreshes citation counts / metadata to whatever OpenAlex currently reports.

Usage:
    python -m ingestion.ingest_openalex
"""

import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Author, Paper, PaperAuthor, PaperTopic, Topic  # noqa: E402

OPENALEX_BASE_URL = "https://api.openalex.org/works"

# Assignment asks for 300-500 papers across two topics.
# 200/topic gives up to 400 total; some overlap between ML and Robotics
# papers is expected and fine (a paper can legitimately belong to both).
TOPICS = ["machine learning", "robotics"]
PAPERS_PER_TOPIC = 200
PER_PAGE = 200
LOOKBACK_DAYS = 730  # "recent" papers = published in the last 2 years
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]} to avoid redistributing
    raw publisher text. Rebuild the plain-text abstract from that index."""
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    if not positions:
        return None
    max_pos = max(positions)
    return " ".join(positions.get(i, "") for i in range(max_pos + 1))


def fetch_papers_for_topic(client: httpx.Client, topic: str, limit: int) -> list[dict]:
    """Cursor-paginate through OpenAlex 'works' filtered by topic and recency.

    Bounds both ends of the date range: OpenAlex includes "forthcoming" /
    in-press articles with future placeholder publication dates, and since
    we sort by publication_date:desc those would otherwise dominate the
    top of "recent" results. Capping to_publication_date at today excludes
    them so results are genuinely already-published recent papers.
    """
    since = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    until = date.today().isoformat()
    results: list[dict] = []
    cursor = "*"

    while len(results) < limit and cursor:
        params = {
            "filter": f"default.search:{topic},from_publication_date:{since},to_publication_date:{until}",
            "sort": "publication_date:desc",
            "per-page": min(PER_PAGE, limit - len(results)),
            "cursor": cursor,
            "select": "id,title,display_name,abstract_inverted_index,"
            "publication_year,doi,cited_by_count,authorships",
        }
        if settings.openalex_api_key:
            params["api_key"] = settings.openalex_api_key

        data = None
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            resp = client.get(OPENALEX_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                break
            if resp.status_code in (429, 500, 502, 503) and attempt < MAX_RETRIES:
                print(
                    f"  [{topic}] got HTTP {resp.status_code}, retrying "
                    f"(attempt {attempt}/{MAX_RETRIES})..."
                )
                time.sleep(2**attempt)
                continue
            # Non-retryable error, or retries exhausted: surface it loudly
            # instead of silently returning a partial/empty result set.
            last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"
            break

        if data is None:
            print(
                f"  [{topic}] FAILED to fetch after {MAX_RETRIES} attempts. "
                f"Last error: {last_error}. Got {len(results)} papers before failing."
            )
            break

        batch = data.get("results", [])
        results.extend(batch)
        cursor = data.get("meta", {}).get("next_cursor")
        if not batch:
            break
        time.sleep(0.1)  # be a good citizen

    return results[:limit]


def get_or_create_author(db, openalex_author_id: str, name: str) -> Author:
    author = db.query(Author).filter_by(openalex_id=openalex_author_id).first()
    if author:
        if author.name != name:
            author.name = name
        return author
    author = Author(openalex_id=openalex_author_id, name=name)
    db.add(author)
    db.flush()
    return author


def get_or_create_topic(db, name: str) -> Topic:
    topic = db.query(Topic).filter_by(name=name).first()
    if topic:
        return topic
    topic = Topic(name=name)
    db.add(topic)
    db.flush()
    return topic


def replace_paper_authors(db, paper: Paper, authorships: list[dict]) -> None:
    """Fully rebuild this paper's author links in correct order. Idempotent:
    re-running with the same authorship data produces the same end state.

    Note: OpenAlex can list the same author more than once in `authorships`
    - one entry per institutional affiliation - so we de-duplicate by
    author id, keeping the first (earliest-position) occurrence.
    """
    for link in list(paper.author_links):
        db.delete(link)
    db.flush()

    seen_author_ids: set[str] = set()
    position = 0
    for authorship in authorships:
        author_info = authorship.get("author") or {}
        raw_id = author_info.get("id")
        name = author_info.get("display_name")
        if not raw_id or not name:
            continue
        openalex_author_id = raw_id.rstrip("/").split("/")[-1]
        if openalex_author_id in seen_author_ids:
            continue
        seen_author_ids.add(openalex_author_id)
        author = get_or_create_author(db, openalex_author_id, name)
        db.add(
            PaperAuthor(
                paper_id=paper.id, author_id=author.id, author_position=position
            )
        )
        position += 1
    db.flush()


def upsert_paper_topic_link(db, paper: Paper, topic: Topic, score: float) -> None:
    link = db.query(PaperTopic).filter_by(paper_id=paper.id, topic_id=topic.id).first()
    if link:
        link.score = score
    else:
        db.add(PaperTopic(paper_id=paper.id, topic_id=topic.id, score=score))
    db.flush()


def upsert_work(db, work: dict, topic_name: str) -> Paper:
    raw_id = work["id"].rstrip("/").split("/")[-1]
    title = work.get("title") or work.get("display_name") or "Untitled"
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    year = work.get("publication_year")
    doi = work.get("doi")
    citation_count = work.get("cited_by_count", 0) or 0

    paper = db.query(Paper).filter_by(openalex_id=raw_id).first()
    if paper is None:
        paper = Paper(
            openalex_id=raw_id,
            title=title,
            abstract=abstract,
            publication_year=year,
            doi=doi,
            citation_count=citation_count,
        )
        db.add(paper)
        db.flush()
    else:
        paper.title = title
        paper.abstract = abstract
        paper.publication_year = year
        paper.doi = doi
        paper.citation_count = citation_count

    replace_paper_authors(db, paper, work.get("authorships") or [])

    topic = get_or_create_topic(db, topic_name)
    # OpenAlex doesn't give a per-search relevance score in this response
    # shape, so we use a constant weight of 1.0 for "matched this topic
    # search". Papers matching both searches will have two topic links.
    upsert_paper_topic_link(db, paper, topic, score=1.0)

    return paper


def run() -> None:
    db = SessionLocal()
    total_seen = 0
    total_new = 0
    try:
        with httpx.Client() as client:
            for topic_name in TOPICS:
                print(
                    f"Fetching up to {PAPERS_PER_TOPIC} papers for topic '{topic_name}'..."
                )
                works = fetch_papers_for_topic(client, topic_name, PAPERS_PER_TOPIC)
                print(f"  Retrieved {len(works)} works from OpenAlex")

                for work in works:
                    raw_id = work["id"].rstrip("/").split("/")[-1]
                    existed = (
                        db.query(Paper.id).filter_by(openalex_id=raw_id).first()
                        is not None
                    )
                    upsert_work(db, work, topic_name)
                    total_seen += 1
                    if not existed:
                        total_new += 1
                db.commit()
        print(
            f"Done. Processed {total_seen} paper records, {total_new} newly inserted."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
