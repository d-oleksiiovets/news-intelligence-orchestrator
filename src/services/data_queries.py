import pandas as pd
from sqlalchemy import select, func
import datetime

from src.database.db import get_session
from src.database.models.article_entities import ArticleEntities
from src.database.models.article_analysis import ArticleAnalysis 
from src.database.models.articles import Articles
from src.database.models.entities import Entities
from src.database.models.events import Events
from src.database.models.sources import Sources

def fetch_metrics() -> dict:
    country_sentiment_subq = (
        select(
            ArticleAnalysis.event_id,
            Entities.iso_code,
            func.avg(ArticleEntities.sentiment).label("avg_sentiment")
        )
        .join(ArticleEntities, ArticleEntities.article_id == ArticleAnalysis.article_id)
        .join(Entities, Entities.id == ArticleEntities.entity_id)
        .group_by(ArticleAnalysis.event_id, Entities.iso_code, Entities.name)
        .subquery()
    )

    with get_session() as session:
        total_events_stmt = select(func.count(func.distinct(ArticleAnalysis.event_id)))
        total_events = session.execute(total_events_stmt).scalar() or 0

        kpi_stmt = select(
            func.avg(country_sentiment_subq.c.avg_sentiment).label("avg_sentiment"),
            func.count(func.distinct(country_sentiment_subq.c.iso_code)).label("unique_countries")
        )
        kpi_res = session.execute(kpi_stmt).one()

        return {
            "total_events": total_events,
            "avg_sentiment": kpi_res.avg_sentiment or 0,
            "unique_countries": kpi_res.unique_countries or 0
        }

def fetch_map_and_news_data(event_id: str = "ALL") -> tuple[pd.DataFrame, pd.DataFrame]:
    map_stmt = (
        select(
            Entities.iso_code,
            Entities.name,
            func.avg(ArticleEntities.sentiment).label("avg_sentiment"),
            func.count(ArticleEntities.entity_id).label("mentions")
        )
        .join(ArticleEntities, Entities.id == ArticleEntities.entity_id)
    )

    if event_id != "ALL":
        map_stmt = map_stmt.join(ArticleAnalysis, ArticleEntities.article_id == ArticleAnalysis.article_id)
        map_stmt = map_stmt.where(ArticleAnalysis.event_id == int(event_id))
        
    map_stmt = map_stmt.group_by(Entities.iso_code, Entities.name)

    news_stmt = (
        select(
            ArticleAnalysis.event_id,
            Events.topic_name,
            Entities.iso_code,
            Articles.url,
            Articles.title,
            Sources.name.label("source_name"),
            Articles.published_at
        )
        .join(Articles, Articles.id == ArticleAnalysis.article_id)
        .join(ArticleEntities, ArticleEntities.article_id == Articles.id) 
        .join(Entities, Entities.id == ArticleEntities.entity_id)
        .join(Sources, Sources.id == Articles.source_id)
        .join(Events, Events.id == ArticleAnalysis.event_id)
    )

    if event_id != "ALL":
        news_stmt = news_stmt.where(ArticleAnalysis.event_id == int(event_id))
        
    news_stmt = news_stmt.group_by(
        ArticleAnalysis.event_id,
        Events.topic_name,
        Entities.iso_code,
        Articles.url,
        Articles.title,
        Sources.name,
        Articles.published_at
    )

    with get_session() as session:
        map_result = session.execute(map_stmt).all()
        news_result = session.execute(news_stmt).all()

    map_df = pd.DataFrame(map_result, columns=["iso_code", "name", "avg_sentiment", "mentions"])

    news_columns = [
        "event_id", "topic_name", "iso_code", "url", 
        "title", "source_name", "published_at"
    ]
    news_df = pd.DataFrame(news_result, columns=news_columns)

    return map_df, news_df

def fetch_mix_max_date():
    stmt = select(
        func.min(Articles.published_at),
        func.max(Articles.published_at)
    )

    with get_session() as session:
        result = session.execute(stmt).one()

    return result

def fetch_timeline_data(
    freq: str = "day", 
    start_date: datetime.date = None, 
    end_date: datetime.date = None,
    event_id: str = "ALL"
) -> pd.DataFrame:

    df_countries_stmt = select(
        ArticleAnalysis.event_id,
        func.avg(ArticleEntities.sentiment).label("country_avg_sentiment")
    ).join(ArticleEntities, ArticleEntities.article_id == ArticleAnalysis.article_id)

    if event_id != "ALL":
        df_countries_stmt = df_countries_stmt.where(ArticleAnalysis.event_id == int(event_id))

    country_sentiment_subq = df_countries_stmt.group_by(ArticleAnalysis.event_id, ArticleEntities.entity_id).subquery()

    event_sentiment_subq = select(
        country_sentiment_subq.c.event_id,
        func.avg(country_sentiment_subq.c.country_avg_sentiment).label("event_sentiment")
    ).group_by(country_sentiment_subq.c.event_id).subquery()

    news_stmt = select(
        ArticleAnalysis.event_id,
        Articles.published_at,
    ).join(Articles, Articles.id == ArticleAnalysis.article_id) \
     .join(ArticleEntities, ArticleEntities.article_id == Articles.id)

    if event_id != "ALL":
        news_stmt = news_stmt.where(ArticleAnalysis.event_id == int(event_id))

    if start_date:
        news_stmt = news_stmt.where(func.date(Articles.published_at) >= start_date)
    if end_date:
        news_stmt = news_stmt.where(func.date(Articles.published_at) <= end_date)

    df_news_subq = news_stmt.group_by(
        ArticleAnalysis.event_id, Articles.id, ArticleEntities.entity_id 
    ).subquery()

    stmt = select(
        func.date_trunc(freq, df_news_subq.c.published_at).label('date'),
        func.avg(event_sentiment_subq.c.event_sentiment).label("avg_sentiment"),
        func.count(df_news_subq.c.published_at).label("news_count")
    ).join(
        event_sentiment_subq, event_sentiment_subq.c.event_id == df_news_subq.c.event_id
    ).group_by('date').order_by('date')

    with get_session() as session:
        result = session.execute(stmt).all()

    return pd.DataFrame(result, columns=["date", "avg_sentiment", "news_count"])

def fetch_events_list() -> dict:
    stmt = (
        select(Events.id, Events.topic_name)
        .join(ArticleAnalysis, ArticleAnalysis.event_id == Events.id)
        .group_by(Events.id, Events.topic_name)
        .order_by(Events.id.desc())
    )
    with get_session() as session:
        result = session.execute(stmt).all()
        return {str(row.id): f"{row.id}: {row.topic_name}" for row in result}
    
def fetch_barchart_data() -> pd.DataFrame:
    stmt = (
        select(
            Entities.iso_code,
            Entities.name,
            func.count().label("mentions"),
            func.sum(ArticleEntities.sentiment).label("total_sent_score"),
            func.avg(ArticleEntities.sentiment).label("avg_sentiment")
        )
        .join(ArticleEntities, ArticleEntities.entity_id == Entities.id)
        .group_by(Entities.iso_code, Entities.name)
    )
    with get_session() as session:
        result = session.execute(stmt).all()
    
    return pd.DataFrame(result, columns=["iso_code", "name", "mentions", "total_sent_score", "avg_sentiment"])