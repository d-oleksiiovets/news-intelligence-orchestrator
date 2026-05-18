from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from src.config.logger import StatusLog
from src.config.settings import settings

from src.database.models.articles import Articles
from src.database.models.article_entities import ArticleEntities
from src.database.models.entities import Entities
from src.database.models.article_analysis import ArticleAnalysis
from src.database.models.events import Events
from src.database.models.sources import Sources

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        StatusLog.fail(f"Transaction failed, rolled back. Error: {e}")
        raise
    finally:
        session.close()

def check_db_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        StatusLog.success("Successfully connected to the database.")
    except Exception as e:
        StatusLog.fail(f"Could not connect to the database: {e}")
        raise