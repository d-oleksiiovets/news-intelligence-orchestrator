from sqlalchemy import ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.articles import Articles
    from src.database.models.entities import Entities

class ArticleEntities(Base):
    __tablename__ = "article_entities"

    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), primary_key=True, index=True)
    sentiment: Mapped[float] = mapped_column(Float, index=True)

    article: Mapped["Articles"] = relationship(back_populates="entities")
    entity: Mapped["Entities"] = relationship(back_populates="articles")