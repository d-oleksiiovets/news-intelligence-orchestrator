import os
import warnings
import logging

# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# warnings.filterwarnings("ignore", category=UserWarning)
# logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logging.getLogger("httpcore").setLevel(logging.WARNING)

import typer
from pathlib import Path
from alembic.config import Config
from alembic import command
import transformers

from src.utils.load_config import load_config
from src.pipeline_runner import PipelineRunner
from src.dashboard_runner import run_dashboard
from src.scheduler import start_scheduler

# transformers.logging.set_verbosity_error()
# transformers.utils.logging.disable_progress_bar()

app = typer.Typer(help="News Pipeline")
CONFIG = load_config()

def _build_pipeline():
    llm_settings_dir = Path(__file__).parent / "llm_settings"
    active_path = CONFIG.get("active_llm_settings", "v1.yaml")
    llm_settings_path = llm_settings_dir / active_path
    llm_settings = load_config(llm_settings_path)
    return PipelineRunner(CONFIG, llm_settings)

def _run_migration():
    albemic_cfg = Config("alembic.ini")
    command.upgrade(albemic_cfg, "head")

@app.command()
def run():
    _run_migration()
    pipeline = _build_pipeline()

    try:
        pipeline.run()
    except RuntimeError as e:
        typer.echo(f"Pipeline failed: {e}", err=True)
        raise typer.Exit(code=1)

@app.command()
def dashboard(port: int = typer.Option(8501, "--port", "-p"),
              no_browser: bool = typer.Option(False, "--no-browser")
):
    run_dashboard(port=port, browser=not no_browser)

@app.command()
def scheduler():
    _run_migration()
    pipeline = _build_pipeline()
    start_scheduler(pipeline.run, CONFIG)

if __name__ == "__main__":
    app()