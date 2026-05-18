from sqlalchemy import select
from datetime import timedelta
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from src.database.models.articles import Articles
from src.database.models.article_analysis import ArticleAnalysis
from src.database.models.article_entities import ArticleEntities
from src.database.models.events import Events
from src.database.db import get_session
from src.config.logger import StatusLog

def events_group(config: dict):
    StatusLog.info("Starting event grouping...")

    batch_size = config.get("grouping_batch_size", 512)
    distance_threshold = config.get("distance_threshold", 0.15)
    overlap_threshold = config.get("overlap_threshold", 0.5)

    total_processed = 0
    total_matched = 0
    total_created = 0
    batch_num = 0

    while True:
        with get_session() as session:
            batch_num += 1
            StatusLog.info(f"Retrieving articles for batch {batch_num}...")

            stmt = select(ArticleAnalysis).where(
                ArticleAnalysis.event_id.is_(None),
                ArticleAnalysis.embedding.is_not(None)
            ).options(
                selectinload(ArticleAnalysis.article).selectinload(Articles.entities)
            ).limit(batch_size)
            articles = session.scalars(stmt).all()

            if not articles:
                StatusLog.skip("No articles to process. Finishing.")
                break

            StatusLog.info(f"Batch {batch_num}: {len(articles)} articles received for grouping.")

            for article in articles:
                article_entity_ids = {ae.entity_id for ae in article.article.entities}

                distance_expr = ArticleAnalysis.embedding.cosine_distance(article.embedding)
                pub_date = article.article.published_at
                cutoff_start = pub_date - timedelta(hours=48)
                cutoff_end = pub_date + timedelta(hours=48)

                neighbors_stmt = (
                    select(
                        ArticleAnalysis.article_id,
                        ArticleAnalysis.event_id,
                        distance_expr.label("distance"),
                        func.array_agg(ArticleEntities.entity_id).label("entity_ids")
                    )
                    .join(Articles, Articles.id == ArticleAnalysis.article_id)
                    .outerjoin(ArticleEntities, Articles.id == ArticleEntities.article_id)
                    .where(
                        ArticleAnalysis.article_id != article.article_id,
                        ArticleAnalysis.embedding.is_not(None),
                        Articles.published_at.between(cutoff_start, cutoff_end),
                        distance_expr <= distance_threshold
                    )
                    .group_by(ArticleAnalysis.article_id, ArticleAnalysis.event_id, distance_expr)
                    .order_by(distance_expr)
                )
                neighbors = session.execute(neighbors_stmt).all()
                matched_event_id = None

                for n in neighbors:
                    neighbor_entities = set(n.entity_ids or [])

                    if not article_entity_ids or not neighbor_entities:
                        if n.event_id is not None:
                            matched_event_id = n.event_id
                            break
                        continue

                    overlap = len(article_entity_ids & neighbor_entities) / len(article_entity_ids | neighbor_entities)

                    if overlap >= overlap_threshold:
                        if n.event_id is not None:
                            matched_event_id = n.event_id
                            break  

                if matched_event_id is not None:
                    article.event_id = matched_event_id
                    total_matched += 1
                else:
                    new_event = Events(topic_name="TBD")
                    session.add(new_event)
                    session.flush()
                    article.event_id = new_event.id
                    total_created += 1

                total_processed += 1

            session.commit()
            StatusLog.success(f"Batch {batch_num}: {len(articles)} articles committed.")

    StatusLog.success(f"Event grouping complete. Total processed: {total_processed} (matched: {total_matched}, new events: {total_created}).")