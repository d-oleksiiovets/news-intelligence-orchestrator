from sqlalchemy.dialects.postgresql import insert

from src.database.models.sources import Sources
from src.database.db import get_session
from src.config.logger import StatusLog

def initialize_sources(config: dict) -> None:
    initial_sources = config.get("sources", [])

    if not initial_sources:
        StatusLog.fail("The list of sources in config.yaml is empty or not found.")
        return

    StatusLog.info(f"Syncing {len(initial_sources)} sources with the database...")

    with get_session() as session:
        try:
            stmt = insert(Sources).values(initial_sources)
            do_nothing_stmt = stmt.on_conflict_do_nothing(index_elements=["url"])

            result = session.execute(do_nothing_stmt)
            session.commit()

            inserted_count = result.rowcount

            if inserted_count > 0:
                StatusLog.success(f"Successfully added {inserted_count} new sources.")
            else:
                StatusLog.skip("No new sources were added (all already exist).")

        except Exception as e:
            StatusLog.fail(f"Failed to sync sources. Error: {e}")
            raise 