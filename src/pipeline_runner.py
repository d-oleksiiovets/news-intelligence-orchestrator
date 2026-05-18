from src.database.db import engine, check_db_health
from src.ingestion.sources_init import initialize_sources
from src.ingestion.rss_parser import parser
from src.config.logger import StatusLog
from src.services.categorize_articles import categorize_articles
from src.services.country_sentiment_extraction import country_sentiment_extraction
from src.services.embedding_sync import process_unembedded_articles
from src.services.events_grouping import events_group
from src.ml.llm_factory import create_llm_engine

class PipelineRunner:
    def __init__(self, config: dict, llm_settings: dict):
        self.config = config
        self.llm_settings = llm_settings
        self.llm_engine = create_llm_engine(self.llm_settings)

    def _check_database(self):
        StatusLog.info("Checking database health...")
        try:
            check_db_health()
            StatusLog.success("Database ready.")
        except Exception as e:
            raise RuntimeError(f"Database unavailable: {e}") from e

    def run(self, job_id=None):
        if job_id:
            StatusLog.info(f"Starting pipeline for job: {job_id}...")
        else:
            StatusLog.info("Starting pipeline...")
            
        self._check_database()

        steps = [
            ("Initialize Sources", initialize_sources, (self.config,)),
            ("Run Parser", parser, ()),
            ("Categorize Articles", categorize_articles, (self.config,)),
            ("Country & Sentiment Extraction", country_sentiment_extraction, (self.config, self.llm_engine)),
            ("Embedding Generation", process_unembedded_articles, (self.config,)),
            ("Events Grouping", events_group, (self.config,))
        ]

        for name, func, args in steps:
            StatusLog.info(f"--- {name} ---")
            try:
                func(*args) 
                StatusLog.success(f"{name} completed successfully.")
            except Exception as e:
                raise RuntimeError(f"Database unavailable: {e}") from e