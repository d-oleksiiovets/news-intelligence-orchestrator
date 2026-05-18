from pathlib import Path

import requests

from src.config.logger import StatusLog


def ensure_model_file(model_path: str, model_url: str | None, timeout: int = 60) -> Path:
    path = Path(model_path)

    if path.exists():
        StatusLog.info(f"LLM model already exists: {path}")
        return path

    if not model_url:
        raise RuntimeError(
            f"LLM model not found at '{path}' and 'local.model_url' is not set in llm settings."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".part")

    StatusLog.info(f"Downloading LLM model from {model_url}...")
    with requests.get(model_url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with open(temp_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    temp_path.replace(path)
    StatusLog.success(f"LLM model downloaded: {path}")
    return path
