from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.database.models.articles import Articles
from src.database.models.article_entities import ArticleEntities
from src.database.models.entities import Entities
from src.database.db import get_session
from src.config.logger import StatusLog
from src.ml.base_llm import BaseLLMEngine
from src.utils.countries_constants import COUNTRIES_NAME_TO_CODE

def _process_article(session, article: Articles, engine: BaseLLMEngine) -> bool:
    title_preview = article.title[:50]
    StatusLog.info(f"Processing article id={article.id} title='{title_preview}...'")

    result = engine.extract_news(f"{article.title}. {article.summary}")

    if not result or not result.entities:
        StatusLog.skip(f"No entities found for article id={article.id}. Skipping.")
        article.is_llm_processed = True
        return False
    
    entities_by_name = {e.country_name: e for e in result.entities}

    entities_payload = [
        {"name": e.country_name, "iso_code": COUNTRIES_NAME_TO_CODE[e.country_name]}
        for e in entities_by_name.values()
    ]
    session.execute(
        insert(Entities)
        .values(entities_payload)
        .on_conflict_do_nothing(index_elements=["name"])
    )
    StatusLog.info(f"Upserted {len(entities_payload)} entities.")

    session.flush()

    country_names = list(entities_by_name.keys())
    db_entities = session.scalars(
        select(Entities).where(Entities.name.in_(country_names))
    ).all()
    name_to_id = {ent.name: ent.id for ent in db_entities}

    article_entities_payload = [
        {
            "article_id": article.id,
            "entity_id": name_to_id[entity.country_name],
            "sentiment": entity.sentiment,
        }
        for entity in entities_by_name.values()
        if entity.country_name in name_to_id
    ]

    if article_entities_payload:
        session.execute(
            insert(ArticleEntities)
            .values(article_entities_payload)
            .on_conflict_do_nothing(index_elements=["article_id", "entity_id"])
        )
        StatusLog.info(
            f"Linked {len(article_entities_payload)} entities to article id={article.id}."
        )

    article.is_llm_processed = True
    return True

def country_sentiment_extraction(main_config: dict, engine: BaseLLMEngine) -> None:
    batch_size = main_config.get("llm_batch_size", 32)

    while True:
        with get_session() as session:
            articles = session.scalars(
                select(Articles)
                .where(
                    (Articles.categories != {"ignored"})
                    & (Articles.is_llm_processed.is_(False))  
                )
                .limit(batch_size)
            ).all()

            if not articles:
                StatusLog.skip("No articles to update. Finishing.")
                break

            StatusLog.info(f"Fetched {len(articles)} articles for processing.")
            processed_count = 0

            for article in articles:
                try:
                    success = _process_article(session, article, engine)
                    session.commit()
                    if success:
                        processed_count += 1
                        StatusLog.success(f"Processed article id={article.id} successfully.")
                except Exception as e:
                    session.rollback()
                    StatusLog.fail(f"Failed to process article id={article.id}. Error: {e}")
                    continue

            StatusLog.success(
                f"Batch completed: {processed_count}/{len(articles)} articles processed."
            )