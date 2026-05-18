from typing import List
from datetime import datetime
from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.article_analysis import ArticleAnalysis

class Events(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article_analysis: Mapped[List["ArticleAnalysis"]] = relationship(back_populates="event")