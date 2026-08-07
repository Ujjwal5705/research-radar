from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    openalex_id: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String, index=True)

    paper_links: Mapped[list["PaperAuthor"]] = relationship(back_populates="author")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    paper_links: Mapped[list["PaperTopic"]] = relationship(back_populates="topic")


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True)
    openalex_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_year: Mapped[int | None] = mapped_column(
        Integer, index=True, nullable=True
    )
    doi: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Association objects (not plain secondary tables) because we need
    # extra columns: author_position (author order matters for display)
    # and topic relevance score (returned by OpenAlex).
    author_links: Mapped[list["PaperAuthor"]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
        order_by="PaperAuthor.author_position",
    )
    topic_links: Mapped[list["PaperTopic"]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
        order_by="PaperTopic.score.desc()",
    )


class PaperAuthor(Base):
    """Join table: which authors wrote which paper, and in what order."""

    __tablename__ = "paper_authors"

    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), primary_key=True)
    author_position: Mapped[int] = mapped_column(Integer, default=0)

    paper: Mapped["Paper"] = relationship(back_populates="author_links")
    author: Mapped["Author"] = relationship(back_populates="paper_links")


class PaperTopic(Base):
    """Join table: which topics a paper belongs to, and OpenAlex's relevance score."""

    __tablename__ = "paper_topics"

    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)

    paper: Mapped["Paper"] = relationship(back_populates="topic_links")
    topic: Mapped["Topic"] = relationship(back_populates="paper_links")
