from typing import List, Optional
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Text, ARRAY, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList
from typing import TYPE_CHECKING

from src.database.models.base import Base
from src.database.models.sources import Sources
from src.database.models.article_analysis import ArticleAnalysis

if TYPE_CHECKING:
    from src.database.models.article_entities import ArticleEntities


class Articles(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    categories: Mapped[List[str]] = mapped_column(MutableList.as_mutable(ARRAY(Text)), default=list)
    is_llm_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_embedding_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    entities: Mapped[List["ArticleEntities"]] = relationship(back_populates="article", cascade="all, delete-orphan")
    source: Mapped["Sources"] = relationship(back_populates="articles")
    analysis: Mapped["ArticleAnalysis"] = relationship(back_populates="article", uselist=False, cascade="all, delete-orphan")