from typing import List
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.article_entities import ArticleEntities

class Entities(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, index=True)
    iso_code: Mapped[str] = mapped_column(Text, index=True)   

    articles: Mapped[List["ArticleEntities"]] = relationship(back_populates="entity")