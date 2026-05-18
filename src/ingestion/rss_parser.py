import feedparser
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, update

from src.database.models.articles import Articles
from src.database.models.sources import Sources
from src.database.db import get_session
from src.config.logger import StatusLog

def _clean_html(html):
    if not html:
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)

def parser():
    with get_session() as session:
        sources_db = session.scalars(select(Sources)).all()
        sources = [{"id": s.id, "url": s.url} for s in sources_db]

    StatusLog.info(f"Starting a survey of {len(sources)} sources...")

    new_articles_data = []
    successful_source_ids = []

    for source in sources:
        StatusLog.info(f"Processing: {source['url']}")
        try:
            feed = feedparser.parse(source['url'])
        except Exception as e:
            StatusLog.fail(f"Network error for {source['url']}: {e}")
            continue

        status = feed.get("status")
        if status not in (200, 301, 302) or feed.bozo:
            StatusLog.fail(f"Fetch failed for {source['url']} (status: {status})")
            continue        
        successful_source_ids.append(source['id'])

        for entry in feed.entries:
            raw_link = entry.get("link", "")
            if not raw_link:
                continue

            article_url = raw_link

            summary_raw = ""
            if "summary_detail" in entry and "value" in entry.summary_detail:
                summary_raw = entry.summary_detail["value"]
            elif "summary" in entry:
                summary_raw = entry.summary

            if entry.get("published_parsed"):
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif entry.get("updated_parsed"):
                published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)

            new_articles_data.append({
                "source_id": source['id'],
                "title": entry.get("title", "No Title"),
                "summary": _clean_html(summary_raw),
                "url": article_url,
                "published_at": published_at
            })

    if new_articles_data or successful_source_ids:
        with get_session() as session:
            try:
                if successful_source_ids:
                    session.execute(
                        update(Sources)
                        .where(Sources.id.in_(successful_source_ids))
                        .values(last_fetched_at=datetime.now(timezone.utc))
                    )
                inserted_count = 0
                if new_articles_data:
                    stmt = insert(Articles).values(new_articles_data)
                    do_nothing_stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
                    
                    result = session.execute(do_nothing_stmt)
                    inserted_count = result.rowcount

                session.commit()

                if inserted_count > 0:
                    StatusLog.success(f"Successfully added {inserted_count} new articles.")
                else:
                    StatusLog.skip("No new articles to add.")

            except Exception as e:
                session.rollback()
                StatusLog.fail(f"Database error during insert: {e}")