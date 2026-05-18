from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.models.articles import Articles
from src.database.models.article_entities import ArticleEntities
from src.database.models.article_analysis import ArticleAnalysis
from src.database.db import get_session
from src.config.logger import StatusLog
from src.ml.embedding_engine import EmbeddingEngine


def _get_common_sentiment(sentiments: list[float]) -> str:
    if not sentiments:
        return "unknown"
    
    neg_score = sum(abs(s) for s in sentiments if s < -0.2)
    pos_score = sum(abs(s) for s in sentiments if s > 0.2)
    
    if neg_score > pos_score:
        return "Negative"
    elif pos_score > neg_score:
        return "Positive"
    return "Neutral"
    
def process_unembedded_articles(config: dict):
    engine = EmbeddingEngine(config)

    StatusLog.info("Starting embedding processing...")
    batch_num = 0
    total_processed = 0

    while True:
        with get_session() as session:
            StatusLog.info("Retrieving articles from the database...")
            stmt = select(Articles).where(
                (Articles.categories != {"ignored"})
                & (Articles.is_embedding_processed.is_(False))
            ).options(
                selectinload(Articles.entities).selectinload(ArticleEntities.entity)
            ).limit(engine.batch_size)

            articles = session.scalars(stmt).all()

            if not articles:
                StatusLog.skip("No articles to update. Finishing.")
                break

            batch_num += 1
            StatusLog.info(f"Batch {batch_num}: {len(articles)} articles received for encoding.")

            texts = [f"{a.title}. {a.summary}" for a in articles]
            embeddings = engine.predict(texts)

            for article, emb in zip(articles, embeddings):
                article_sentiments = [ae.sentiment for ae in article.entities]

                if article.analysis is not None:
                    article.analysis.embedding = emb.tolist()
                else:
                    session.add(ArticleAnalysis(
                        article_id=article.id,
                        sentiment_label=_get_common_sentiment(article_sentiments),
                        embedding=emb.tolist(),
                    ))
                article.is_embedding_processed = True

            session.commit()
            total_processed += len(articles)
            StatusLog.success(f"Batch {batch_num}: {len(articles)} articles committed.")

    StatusLog.success(f"Embedding complete. Total processed: {total_processed}.")

