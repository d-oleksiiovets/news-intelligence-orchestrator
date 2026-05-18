from typing import List, Optional
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from typing import TYPE_CHECKING

from src.database.models.base import Base
if TYPE_CHECKING:
    from src.database.models.articles import Articles
    from src.database.models.events import Events

class ArticleAnalysis(Base):
    __tablename__ = "article_analysis"

    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    sentiment_label: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("events.id"), index=True, nullable=True)
    
    article: Mapped["Articles"] = relationship(back_populates="analysis")
    event: Mapped[Optional["Events"]] = relationship(back_populates="article_analysis")