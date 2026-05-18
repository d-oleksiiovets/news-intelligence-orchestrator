from sqlalchemy import select

from src.database.db import get_session
from src.database.models.articles import Articles
from src.ml.zero_shot_engine import ZeroShotEngine
from src.config.logger import StatusLog

def categorize_articles(config: dict):
    engine = ZeroShotEngine(config)

    while(True):
        with get_session() as session:
            try:
                stmt = select(Articles).where(
                    (Articles.categories.is_(None)) | (Articles.categories == [])
                ).limit(engine.batch_size)

                StatusLog.info("Retrieving articles from the database...")
                articles_to_update = session.scalars(stmt).all() 

                if not articles_to_update:
                    StatusLog.skip("No articles to update. Finishing.")
                    break

                StatusLog.info(f"{len(articles_to_update)} articles received for update.")
                title_summary_list = []
                for article in articles_to_update:
                    title_summary_list.append(f"{article.title}. {article.summary}")

                result_lists = engine.predict(title_summary_list)
                if len(articles_to_update) != len(result_lists):
                    raise ValueError(
                            f"Sanity check failed: {len(articles_to_update)} articles "
                            f"but got {len(result_lists) if result_lists else 0} predictions."
                        )

                for article, cats in zip(articles_to_update, result_lists):
                    article.categories = cats

                session.commit()
                StatusLog.success(f"{len(articles_to_update)} articles were successfully updated.")

            except Exception as e:
                session.rollback()
                StatusLog.fail(f"Failed to process batch. Error: {e}")
                break