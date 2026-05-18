import instructor
from openai import OpenAI
from typing import Optional

from src.config.logger import StatusLog
from src.config.settings import settings
from src.domain.news_analysis import NewsAnalysis
from src.ml.base_llm import BaseLLMEngine

class RemoteLLMEngine(BaseLLMEngine):
    def __init__(self, llm_settings: dict):
        self.system_prompt = llm_settings.get("system_prompt", "")
        self.temperature = llm_settings.get("model", {}).get("temperature", 0.0)
        self.model_name = llm_settings["remote"]["model_name"]
        
        if not settings.API_KEY or not settings.API_KEY.strip():
            raise ValueError("API_KEY is not configured. Please set a valid API key in environment variables.")

        StatusLog.info(f"Initializing LLM Engine with model {self.model_name}...")

        openai_client = OpenAI(
            base_url=llm_settings["remote"]["url"],
            api_key=settings.API_KEY.strip()
        )
        self.client = instructor.from_openai(openai_client, mode=instructor.Mode.MD_JSON)
        StatusLog.success("LLM Engine initialized successfully.")

    def extract_news(self, text_to_analyze: str) -> Optional[NewsAnalysis]:
        try:
            return self.client.chat.completions.create(
                model=self.model_name,
                response_model=NewsAnalysis,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text_to_analyze},
                ],
                max_retries=2,
                temperature=self.temperature,
            )
        except Exception as e:
            StatusLog.fail(f"LLM Extraction failed: {e}")
            return None