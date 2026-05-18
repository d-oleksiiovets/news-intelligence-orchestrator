from typing import List
from datetime import datetime
from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.articles import Articles

class Sources(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles: Mapped[List["Articles"]] = relationship(back_populates="source")